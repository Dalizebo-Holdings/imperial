from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
import json
from typing import Any


LEVELS = {
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
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
    "provider_credentials",
    "card_number",
    "cvv",
    "cvc",
    "pan",
}


class StructuredLoggingError(ValueError):
    pass


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        output = {}
        for key, item in value.items():
            if str(key).strip().lower() in SENSITIVE_KEYS:
                output[key] = "[REDACTED]"
            else:
                output[key] = redact(item)
        return output

    if isinstance(value, list):
        return [redact(item) for item in value]

    if isinstance(value, tuple):
        return [redact(item) for item in value]

    return value


@dataclass(frozen=True)
class StructuredLogRecord:
    timestamp: str
    level: str
    event: str
    correlation_id: str
    organization_id: str | None = None
    actor_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    fields: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if self.level not in LEVELS:
            raise StructuredLoggingError(
                f"unsupported log level: {self.level}"
            )
        if not self.event.strip():
            raise StructuredLoggingError(
                "event must not be empty"
            )
        if not self.correlation_id.strip():
            raise StructuredLoggingError(
                "correlation_id must not be empty"
            )
        try:
            json.dumps(
                self.fields,
                sort_keys=True,
                separators=(",", ":"),
            )
        except (TypeError, ValueError) as exc:
            raise StructuredLoggingError(
                "log fields must be JSON-compatible"
            ) from exc

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        data = asdict(self)
        data["fields"] = redact(self.fields)
        return data


class InMemoryStructuredLogSink:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def emit(
        self,
        *,
        level: str,
        event: str,
        correlation_id: str,
        organization_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        fields: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        record = StructuredLogRecord(
            timestamp=(
                timestamp
                or datetime.now(timezone.utc).isoformat()
            ),
            level=str(level).strip().upper(),
            event=event,
            correlation_id=correlation_id,
            organization_id=organization_id,
            actor_id=actor_id,
            trace_id=trace_id,
            span_id=span_id,
            fields=redact(fields or {}),
        )
        data = record.to_dict()
        self.records.append(data)
        return data
