from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from types import TracebackType
from typing import Any, Callable, Mapping, Sequence, Self

from kernel.observability.logging import (
    InMemoryStructuredLogSink,
    StructuredLogRecord,
    redact,
)


class OutboxObservabilityError(ValueError):
    pass


OBSERVABLE_SOURCE_SERVICE = "outbox_worker"

DELIVERED_EVENT = "outbox.published"
RETRY_SCHEDULED_EVENT = "outbox.retry_scheduled"
DEAD_LETTER_EVENT = "outbox.dead_letter"
CLAIMED_EVENT = "outbox.claimed"
LEASE_REFRESHED_EVENT = "outbox.lease_refreshed"
LEASE_RELEASED_EVENT = "outbox.lease_released"
CLAIM_REJECTED_EVENT = "outbox.claim_rejected"


SENSITIVE_OUTBOX_FIELDS = {
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


def _safe_outbox_fields(fields: Mapping[str, Any]) -> dict[str, Any]:
    return redact(dict(fields))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class OutboxEventLogFact:
    event_id: str
    organization_id: str
    workspace_id: str | None
    project_id: str | None
    environment_id: str | None
    event_type: str
    event_version: str
    correlation_id: str
    resource_type: str
    resource_id: str
    attempt_count: int
    max_attempts: int
    subscription_id: str | None
    delivery_id: str | None
    error_code: str | None
    next_attempt_at: str | None
    lock_owner: str | None
    lock_expires_at: str


@dataclass(frozen=True)
class OutboxObservabilityEmitter:
    sink: InMemoryStructuredLogSink
    correlation_id: str
    organization_id: str
    worker_id: str
    lease_seconds: int
    source_service: str = OBSERVABLE_SOURCE_SERVICE

    def validate(self) -> None:
        if not self.correlation_id.strip():
            raise OutboxObservabilityError("correlation_id required")
        if not self.organization_id.strip():
            raise OutboxObservabilityError("organization_id required")
        if not self.worker_id.strip():
            raise OutboxObservabilityError("worker_id required")
        if self.lease_seconds < 1:
            raise OutboxObservabilityError("lease_seconds must be >= 1")
        if self.source_service.strip() != OBSERVABLE_SOURCE_SERVICE:
            raise OutboxObservabilityError(
                f"source_service must be {OBSERVABLE_SOURCE_SERVICE}"
            )

    def emit_claimed(
        self,
        *,
        fact: OutboxEventLogFact,
        worker_id: str | None = None,
    ) -> dict[str, Any]:
        self.validate()
        return self.sink.emit(
            level="INFO",
            event=CLAIMED_EVENT,
            correlation_id=self.correlation_id,
            organization_id=self.organization_id,
            actor_id=worker_id or self.worker_id,
            fields={
                "event_id": fact.event_id,
                "attempt_count": fact.attempt_count,
                "max_attempts": fact.max_attempts,
                "lock_owner": worker_id or self.worker_id,
                "lock_expires_at": (
                    fact.lock_expires_at
                    if isinstance(fact.lock_expires_at, str)
                    else _now_iso()
                ),
                "resource_type": fact.resource_type,
                "resource_id": fact.resource_id,
                "subscription_id": fact.subscription_id,
                "outbox_status": "claimed",
                "outcome": "claimed",
            },
        )

    def emit_lease_refreshed(
        self,
        *,
        fact: OutboxEventLogFact,
    ) -> dict[str, Any]:
        self.validate()
        return self.sink.emit(
            level="INFO",
            event=LEASE_REFRESHED_EVENT,
            correlation_id=self.correlation_id,
            organization_id=self.organization_id,
            actor_id=self.worker_id,
            fields={
                "event_id": fact.event_id,
                "attempt_count": fact.attempt_count,
                "lock_owner": self.worker_id,
                "lock_expires_at": _now_iso(),
                "lease_seconds": self.lease_seconds,
                "resource_type": fact.resource_type,
                "resource_id": fact.resource_id,
                "outbox_status": "active",
                "outcome": "lease_refreshed",
            },
        )

    def emit_lease_released(
        self,
        *,
        fact: OutboxEventLogFact,
    ) -> dict[str, Any]:
        self.validate()
        return self.sink.emit(
            level="INFO",
            event=LEASE_RELEASED_EVENT,
            correlation_id=self.correlation_id,
            organization_id=self.organization_id,
            actor_id=self.worker_id,
            fields={
                "event_id": fact.event_id,
                "attempt_count": fact.attempt_count,
                "lock_owner": self.worker_id,
                "resource_type": fact.resource_type,
                "resource_id": fact.resource_id,
                "outbox_status": "released",
                "outcome": "lease_released",
            },
        )

    def emit_claim_rejected(
        self,
        *,
        reason: str,
        fact: OutboxEventLogFact | None = None,
    ) -> dict[str, Any]:
        self.validate()
        return self.sink.emit(
            level="WARNING",
            event=CLAIM_REJECTED_EVENT,
            correlation_id=self.correlation_id,
            organization_id=self.organization_id,
            actor_id=self.worker_id,
            fields={
                "reason": reason,
                "event_id": fact.event_id if fact else None,
                "attempt_count": fact.attempt_count if fact else None,
                "max_attempts": fact.max_attempts if fact else None,
                "lock_owner": fact.lock_owner if fact else None,
                "resource_type": fact.resource_type if fact else None,
                "resource_id": fact.resource_id if fact else None,
                "outcome": "rejected",
            },
        )

    def emit_delivery_published(
        self,
        *,
        fact: OutboxEventLogFact,
        published_at: str | None = None,
    ) -> dict[str, Any]:
        self.validate()
        return self.sink.emit(
            level="INFO",
            event=DELIVERED_EVENT,
            correlation_id=self.correlation_id,
            organization_id=self.organization_id,
            actor_id=self.worker_id,
            fields={
                "event_id": fact.event_id,
                "delivery_id": fact.delivery_id,
                "subscription_id": fact.subscription_id,
                "attempt_count": fact.attempt_count,
                "max_attempts": fact.max_attempts,
                "published_at": published_at or _now_iso(),
                "resource_type": fact.resource_type,
                "resource_id": fact.resource_id,
                "outbox_status": "PUBLISHED",
                "outcome": "published",
            },
        )

    def emit_retry_scheduled(
        self,
        *,
        fact: OutboxEventLogFact,
        error_code: str,
        next_attempt_at: str,
    ) -> dict[str, Any]:
        self.validate()
        return self.sink.emit(
            level="INFO",
            event=RETRY_SCHEDULED_EVENT,
            correlation_id=self.correlation_id,
            organization_id=self.organization_id,
            actor_id=self.worker_id,
            fields={
                "event_id": fact.event_id,
                "error_code": error_code,
                "attempt_count": fact.attempt_count,
                "max_attempts": fact.max_attempts,
                "next_attempt_at": next_attempt_at,
                "resource_type": fact.resource_type,
                "resource_id": fact.resource_id,
                "outbox_status": "RETRY_PENDING",
                "outcome": "retry_scheduled",
            },
        )

    def emit_dead_letter(
        self,
        *,
        fact: OutboxEventLogFact,
        error_code: str,
    ) -> dict[str, Any]:
        self.validate()
        return self.sink.emit(
            level="ERROR",
            event=DEAD_LETTER_EVENT,
            correlation_id=self.correlation_id,
            organization_id=self.organization_id,
            actor_id=self.worker_id,
            fields={
                "event_id": fact.event_id,
                "error_code": error_code,
                "attempt_count": fact.attempt_count,
                "max_attempts": fact.max_attempts,
                "resource_type": fact.resource_type,
                "resource_id": fact.resource_id,
                "outbox_status": "DEAD_LETTER",
                "outcome": "dead_letter",
            },
        )

    @staticmethod
    def build_fact_from_row(
        row: Mapping[str, Any],
        *,
        subscription_id: str | None = None,
        delivery_id: str | None = None,
        error_code: str | None = None,
        next_attempt_at: str | None = None,
    ) -> OutboxEventLogFact:
        attempt_count = row.get("attempt_count")
        max_attempts = row.get("max_attempts")
        if not isinstance(attempt_count, int) or attempt_count < 1:
            raise OutboxObservabilityError("row attempt_count invalid")
        if not isinstance(max_attempts, int) or max_attempts < attempt_count:
            raise OutboxObservabilityError("row max_attempts invalid")

        lock_expires_at = row.get("lock_expires_at")
        if lock_expires_at is not None and not isinstance(lock_expires_at, str):
            raise OutboxObservabilityError("lock_expires_at must be ISO string")

        return OutboxEventLogFact(
            event_id=_require_text(row, "event_id"),
            organization_id=_require_text(row, "organization_id"),
            workspace_id=_nullable_text(row, "workspace_id"),
            project_id=_nullable_text(row, "project_id"),
            environment_id=_nullable_text(row, "environment_id"),
            event_type=_require_text(row, "event_type"),
            event_version=_require_text(row, "event_version"),
            correlation_id=_require_text(row, "correlation_id"),
            resource_type=_require_text(row, "resource_type"),
            resource_id=_require_text(row, "resource_id"),
            attempt_count=attempt_count,
            max_attempts=max_attempts,
            subscription_id=subscription_id,
            delivery_id=delivery_id,
            error_code=error_code,
            next_attempt_at=next_attempt_at,
            lock_expires_at=(
                lock_expires_at
                if lock_expires_at is not None
                else _now_iso()
            ),
            lock_owner=_nullable_text(row, "lock_owner"),
        )


def _require_text(row: Mapping[str, Any], name: str) -> str:
    value = row.get(name)
    if not isinstance(value, str) or not value.strip():
        raise OutboxObservabilityError(f"row field {name} is invalid")
    return value


def _nullable_text(row: Mapping[str, Any], name: str) -> str | None:
    value = row.get(name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise OutboxObservabilityError(f"row field {name} is invalid")
    return value


class FakeOutboxWorkerTracer:
    def __init__(self, sink: InMemoryStructuredLogSink) -> None:
        self.sink = sink
        self.records: list[dict[str, Any]] = []

    def emit(
        self,
        *,
        level: str,
        event: str,
        correlation_id: str,
        organization_id: str,
        actor_id: str | None = None,
        source_service: str | None = None,
        fields: Mapping[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        record = self.sink.emit(
            level=level,
            event=event,
            correlation_id=correlation_id,
            organization_id=organization_id,
            actor_id=actor_id,
            trace_id=None,
            span_id=None,
            source_service=source_service,
            fields=fields or {},
            timestamp=timestamp,
        )
        self.records.append(record)
        return record
