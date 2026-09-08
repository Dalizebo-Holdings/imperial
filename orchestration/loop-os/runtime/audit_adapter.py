from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
from typing import Any


AUDIT_VERSION = "loop-os-audit-v1"

ALLOWED_EVENT_TYPES = {
    "loop_os.job.claimed",
    "loop_os.job.started",
    "loop_os.job.completed",
    "loop_os.job.retry_pending",
    "loop_os.job.dead_lettered",
    "loop_os.job.authorization_denied",
}

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
    "job_id",
    "correlation_id",
}


class LoopAuditError(ValueError):
    pass


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _sha256(value: Any) -> str:
    return hashlib.sha256(
        _canonical_json(value).encode("utf-8")
    ).hexdigest()


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        result = {}

        for key, item in value.items():
            normalized = str(key).strip().lower()

            if normalized in SENSITIVE_KEYS:
                result[key] = "[REDACTED]"
            else:
                result[key] = redact(item)

        return result

    if isinstance(value, list):
        return [redact(item) for item in value]

    if isinstance(value, tuple):
        return [redact(item) for item in value]

    return value


def validate_event(event: dict) -> None:
    if not isinstance(event, dict):
        raise LoopAuditError("audit event must be an object")

    missing = [
        field
        for field in sorted(REQUIRED_EVENT_FIELDS)
        if not str(event.get(field, "")).strip()
    ]

    if missing:
        raise LoopAuditError(
            "missing audit event fields: " + ", ".join(missing)
        )

    event_type = str(event["event_type"]).strip()

    if event_type not in ALLOWED_EVENT_TYPES:
        raise LoopAuditError(
            f"unsupported Loop OS event type: {event_type}"
        )


def build_record(
    *,
    event: dict,
    previous_hash: str = "",
    recorded_at: str | None = None,
) -> dict:
    validate_event(event)

    sanitized = redact(event)
    timestamp = recorded_at or datetime.now(timezone.utc).isoformat()

    event_identity = {
        "event_type": sanitized["event_type"],
        "job_id": sanitized["job_id"],
        "correlation_id": sanitized["correlation_id"],
        "attempt": sanitized.get("attempt"),
        "status": sanitized.get("status"),
        "retry_at": sanitized.get("retry_at"),
        "error_code": sanitized.get("error_code"),
        "authorization_ref": sanitized.get("authorization_ref"),
    }

    event_id = "loop_audit_" + _sha256(event_identity)[:24]

    record = {
        "audit_version": AUDIT_VERSION,
        "event_id": event_id,
        "recorded_at": timestamp,
        "event": sanitized,
        "previous_hash": previous_hash,
    }

    record["record_hash"] = _sha256(record)
    return record


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
                raise LoopAuditError(
                    f"invalid JSONL at line {line_number}"
                ) from exc

            if not isinstance(record, dict):
                raise LoopAuditError(
                    f"audit record at line {line_number} is not an object"
                )

            records.append(record)

    return records


def append_event(
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


def persist_worker_result(
    path: str | Path,
    *,
    worker_result: Any,
    recorded_at: str | None = None,
) -> list[dict]:
    events = getattr(worker_result, "events", None)

    if not isinstance(events, list):
        raise LoopAuditError(
            "worker_result.events must be a list"
        )

    records = []

    for event in events:
        records.append(
            append_event(
                path,
                event=event,
                recorded_at=recorded_at,
            )
        )

    return records


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

        try:
            validate_event(record["event"])
        except LoopAuditError:
            return {
                "valid": False,
                "index": index,
                "reason": "invalid_event",
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
