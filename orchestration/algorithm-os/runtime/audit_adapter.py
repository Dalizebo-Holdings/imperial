from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
from typing import Any


AUDIT_VERSION = "algorithm-os-audit-v1"

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
}

REQUIRED_EVENT_FIELDS = {
    "event_type",
    "decision_id",
    "decision_request_id",
    "correlation_id",
    "actor_id",
    "organization_id",
    "registry_version",
    "policy_version",
    "risk_class",
    "outcome",
}


class AuditAdapterError(ValueError):
    pass


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _sha256(payload: Any) -> str:
    return hashlib.sha256(
        _canonical_json(payload).encode("utf-8")
    ).hexdigest()


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized = {}

        for key, item in value.items():
            normalized = str(key).strip().lower()

            if normalized in SENSITIVE_KEYS:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = redact(item)

        return sanitized

    if isinstance(value, list):
        return [redact(item) for item in value]

    if isinstance(value, tuple):
        return [redact(item) for item in value]

    return value


def validate_event(event: dict) -> None:
    missing = [
        field
        for field in sorted(REQUIRED_EVENT_FIELDS)
        if not str(event.get(field, "")).strip()
    ]

    if missing:
        raise AuditAdapterError(
            "Missing audit event fields: " + ", ".join(missing)
        )


def build_record(
    *,
    event: dict,
    previous_hash: str = "",
    recorded_at: str | None = None,
) -> dict:
    validate_event(event)

    sanitized_event = redact(event)
    timestamp = recorded_at or datetime.now(timezone.utc).isoformat()

    event_id_material = {
        "decision_id": sanitized_event["decision_id"],
        "event_type": sanitized_event["event_type"],
        "correlation_id": sanitized_event["correlation_id"],
        "outcome": sanitized_event["outcome"],
    }

    event_id = "audit_" + _sha256(event_id_material)[:24]

    body = {
        "audit_version": AUDIT_VERSION,
        "event_id": event_id,
        "recorded_at": timestamp,
        "event": sanitized_event,
        "previous_hash": previous_hash,
    }

    body["record_hash"] = _sha256(body)
    return body


def read_records(path: str | Path) -> list[dict]:
    path = Path(path)

    if not path.exists():
        return []

    records = []

    with path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            stripped = line.strip()

            if not stripped:
                continue

            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise AuditAdapterError(
                    f"Invalid JSONL at line {line_number}"
                ) from exc

            if not isinstance(record, dict):
                raise AuditAdapterError(
                    f"Audit record at line {line_number} is not an object"
                )

            records.append(record)

    return records


def append_record(
    path: str | Path,
    *,
    event: dict,
    recorded_at: str | None = None,
) -> dict:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    existing = read_records(path)
    previous_hash = (
        existing[-1].get("record_hash", "")
        if existing
        else ""
    )

    record = build_record(
        event=event,
        previous_hash=previous_hash,
        recorded_at=recorded_at,
    )

    with path.open("a", encoding="utf-8") as f:
        f.write(_canonical_json(record))
        f.write("\n")

    return record


def verify_records(records: list[dict]) -> dict:
    previous_hash = ""

    for index, record in enumerate(records):
        required = {
            "audit_version",
            "event_id",
            "recorded_at",
            "event",
            "previous_hash",
            "record_hash",
        }

        missing = sorted(required - set(record))

        if missing:
            return {
                "valid": False,
                "index": index,
                "reason": "missing_fields:" + ",".join(missing),
            }

        if record["audit_version"] != AUDIT_VERSION:
            return {
                "valid": False,
                "index": index,
                "reason": "audit_version_mismatch",
            }

        if record["previous_hash"] != previous_hash:
            return {
                "valid": False,
                "index": index,
                "reason": "previous_hash_mismatch",
            }

        material = dict(record)
        supplied_hash = material.pop("record_hash")

        expected_hash = _sha256(material)

        if supplied_hash != expected_hash:
            return {
                "valid": False,
                "index": index,
                "reason": "record_hash_mismatch",
            }

        previous_hash = supplied_hash

    return {
        "valid": True,
        "count": len(records),
        "last_hash": previous_hash,
    }


def verify_file(path: str | Path) -> dict:
    return verify_records(read_records(path))
