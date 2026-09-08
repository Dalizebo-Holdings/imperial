from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
from typing import Any


AUDIT_VERSION = "integrations-os-audit-v1"

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
    "credential_value",
}

REQUIRED_EVENT_FIELDS = {
    "event_type",
    "request_id",
    "connector_id",
    "correlation_id",
}


class IntegrationAuditError(ValueError):
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
        raise IntegrationAuditError(
            "integration audit event must be an object"
        )

    missing = [
        field
        for field in sorted(REQUIRED_EVENT_FIELDS)
        if not str(event.get(field, "")).strip()
    ]

    if missing:
        raise IntegrationAuditError(
            "missing integration audit fields: "
            + ", ".join(missing)
        )

    event_type = str(event["event_type"]).strip()

    if not event_type.startswith("integrations_os.connector."):
        raise IntegrationAuditError(
            f"unsupported integration event type: {event_type}"
        )


def build_record(
    *,
    event: dict,
    previous_hash: str = "",
    recorded_at: str | None = None,
) -> dict:
    validate_event(event)

    sanitized = redact(event)
    timestamp = (
        recorded_at
        or datetime.now(timezone.utc).isoformat()
    )

    event_identity = {
        "event_type": sanitized["event_type"],
        "request_id": sanitized["request_id"],
        "connector_id": sanitized["connector_id"],
        "correlation_id": sanitized["correlation_id"],
        "status": sanitized.get("status"),
        "error_code": sanitized.get("error_code"),
        "provider_status": sanitized.get("provider_status"),
    }

    event_id = (
        "integration_audit_"
        + _sha256(event_identity)[:24]
    )

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
                raise IntegrationAuditError(
                    f"invalid JSONL at line {line_number}"
                ) from exc

            if not isinstance(record, dict):
                raise IntegrationAuditError(
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


def event_from_prepared_call(prepared_call: Any) -> dict:
    request = prepared_call.request
    connector = prepared_call.connector

    return {
        "event_type": "integrations_os.connector.prepared",
        "request_id": request.request_id,
        "connector_id": connector.connector_id,
        "correlation_id": request.correlation_id,
        "connector_version": connector.version,
        "operation": request.operation,
        "organization_id": request.organization_id,
        "authorization_ref": prepared_call.authorization_ref,
        "credential_ref": request.credential_ref,
        "effective_timeout_seconds": (
            prepared_call.effective_timeout_seconds
        ),
        "status": prepared_call.state,
    }


def event_from_response(response: Any) -> dict:
    response.validate()

    event = dict(response.audit_event or {})

    event.setdefault(
        "event_type",
        (
            "integrations_os.connector.completed"
            if response.status == "SUCCESS"
            else "integrations_os.connector.error"
        ),
    )
    event.setdefault("request_id", response.request_id)
    event.setdefault("connector_id", response.connector_id)
    event.setdefault("correlation_id", response.correlation_id)
    event.setdefault("status", response.status)
    event.setdefault(
        "provider_status",
        response.provider_status,
    )
    event.setdefault("retryable", response.retryable)

    if response.error is not None:
        event.setdefault("error_code", response.error.code)
        event.setdefault(
            "provider_code",
            response.error.provider_code,
        )

    validate_event(event)
    return event


def persist_prepared_call(
    path: str | Path,
    *,
    prepared_call: Any,
    recorded_at: str | None = None,
) -> dict:
    return append_event(
        path,
        event=event_from_prepared_call(prepared_call),
        recorded_at=recorded_at,
    )


def persist_response(
    path: str | Path,
    *,
    response: Any,
    recorded_at: str | None = None,
) -> dict:
    return append_event(
        path,
        event=event_from_response(response),
        recorded_at=recorded_at,
    )


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
                "reason": (
                    "missing_fields:"
                    + ",".join(missing)
                ),
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
        except IntegrationAuditError:
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
