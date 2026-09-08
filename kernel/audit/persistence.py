from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path
import json
from typing import Any


AUDIT_VERSION = "kernel-audit-v1"

SENSITIVE_KEYS = {
    "authorization",
    "access_token",
    "refresh_token",
    "api_key",
    "password",
    "secret",
    "client_secret",
    "private_key",
    "cookie",
    "session_token",
    "webhook_secret",
    "card_number",
    "cvv",
    "cvc",
    "pan",
}


class AuditPersistenceError(ValueError):
    pass


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _hash(value: Any) -> str:
    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if str(key).strip().lower() in SENSITIVE_KEYS:
                result[key] = "[REDACTED]"
            else:
                result[key] = redact(item)
        return result

    if isinstance(value, list):
        return [redact(item) for item in value]

    if isinstance(value, tuple):
        return [redact(item) for item in value]

    return value


@dataclass(frozen=True)
class AuditEvent:
    audit_id: str
    organization_id: str
    actor_type: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    timestamp: str
    correlation_id: str
    metadata: dict[str, Any]

    def validate(self) -> None:
        required = {
            "audit_id": self.audit_id,
            "organization_id": self.organization_id,
            "actor_type": self.actor_type,
            "actor_id": self.actor_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
        }

        missing = [
            name
            for name, value in required.items()
            if not str(value).strip()
        ]

        if missing:
            raise AuditPersistenceError(
                "missing audit fields: " + ", ".join(missing)
            )

        try:
            _canonical_json(self.metadata)
        except (TypeError, ValueError) as exc:
            raise AuditPersistenceError(
                "audit metadata must be JSON-compatible"
            ) from exc

    def sanitized(self) -> dict[str, Any]:
        self.validate()
        data = asdict(self)
        data["metadata"] = redact(self.metadata)
        return data


def build_record(
    event: AuditEvent,
    *,
    sequence: int,
    previous_hash: str = "",
) -> dict[str, Any]:
    if not isinstance(sequence, int) or sequence < 1:
        raise AuditPersistenceError(
            "sequence must be an integer >= 1"
        )

    body = {
        "audit_version": AUDIT_VERSION,
        "sequence": sequence,
        "event": event.sanitized(),
        "previous_hash": str(previous_hash),
    }
    body["record_hash"] = _hash(body)
    return body


def read_records(path: str | Path) -> list[dict[str, Any]]:
    target = Path(path)

    if not target.exists():
        return []

    records = []
    with target.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                value = json.loads(text)
            except json.JSONDecodeError as exc:
                raise AuditPersistenceError(
                    f"invalid audit JSONL at line {line_number}"
                ) from exc
            if not isinstance(value, dict):
                raise AuditPersistenceError(
                    f"audit record at line {line_number} is not an object"
                )
            records.append(value)

    return records


def append_event(
    path: str | Path,
    event: AuditEvent,
) -> dict[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    current = read_records(target)
    previous_hash = (
        str(current[-1].get("record_hash", ""))
        if current
        else ""
    )

    record = build_record(
        event,
        sequence=len(current) + 1,
        previous_hash=previous_hash,
    )

    with target.open("a", encoding="utf-8") as handle:
        handle.write(_canonical_json(record))
        handle.write("\n")

    return deepcopy(record)


def verify_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    previous_hash = ""

    for index, record in enumerate(records):
        required = {
            "audit_version",
            "sequence",
            "event",
            "previous_hash",
            "record_hash",
        }

        if not required.issubset(record):
            return {
                "valid": False,
                "index": index,
                "reason": "missing_fields",
            }

        if record["audit_version"] != AUDIT_VERSION:
            return {
                "valid": False,
                "index": index,
                "reason": "version_mismatch",
            }

        if record["sequence"] != index + 1:
            return {
                "valid": False,
                "index": index,
                "reason": "sequence_mismatch",
            }

        if record["previous_hash"] != previous_hash:
            return {
                "valid": False,
                "index": index,
                "reason": "previous_hash_mismatch",
            }

        material = deepcopy(record)
        supplied = material.pop("record_hash")
        expected = _hash(material)

        if supplied != expected:
            return {
                "valid": False,
                "index": index,
                "reason": "record_hash_mismatch",
            }

        previous_hash = supplied

    return {
        "valid": True,
        "count": len(records),
        "last_hash": previous_hash,
    }


def verify_file(path: str | Path) -> dict[str, Any]:
    return verify_records(read_records(path))
