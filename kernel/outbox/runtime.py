from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from types import TracebackType
from typing import Protocol, Self


class OutboxWorkerError(ValueError):
    pass


RowValue = str | int | datetime | None


class OutboxCursor(Protocol):
    @property
    def rowcount(self) -> int: ...

    def __enter__(self) -> Self: ...

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> None: ...

    def execute(self, statement: str, parameters: tuple[RowValue, ...]) -> None: ...

    def fetchall(self) -> Sequence[Mapping[str, RowValue]]: ...


class OutboxConnection(Protocol):
    def cursor(self) -> OutboxCursor: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


@dataclass(frozen=True, slots=True)
class ClaimedOutboxEvent:
    event_id: str
    organization_id: str
    workspace_id: str | None
    project_id: str | None
    environment_id: str | None
    event_type: str
    event_version: str
    correlation_id: str
    actor_type: str
    actor_id: str
    payload: str
    attempt_count: int
    max_attempts: int
    lock_owner: str
    lock_expires_at: datetime


CLAIM_SQL = """
WITH candidate AS (
    SELECT event_id
    FROM kernel.outbox_events
    WHERE published_at IS NULL
      AND outbox_status IN ('COMMITTED', 'RETRY_PENDING')
      AND attempt_count < max_attempts
      AND (
          lock_expires_at IS NULL
          OR lock_expires_at <= clock_timestamp()
      )
      AND next_attempt_at <= clock_timestamp()
      AND organization_id = $3
    ORDER BY next_attempt_at, created_at, event_id
    FOR UPDATE SKIP LOCKED
    LIMIT $4
)
UPDATE kernel.outbox_events AS outbox
SET attempt_count = outbox.attempt_count + 1,
    lock_owner = $1,
    locked_at = clock_timestamp(),
    lock_expires_at = clock_timestamp() + make_interval(secs => $2),
    updated_at = clock_timestamp()
FROM candidate
WHERE outbox.event_id = candidate.event_id
RETURNING outbox.event_id, outbox.organization_id, outbox.workspace_id,
          outbox.project_id, outbox.environment_id, outbox.event_type,
          outbox.event_version, outbox.correlation_id, outbox.actor_type,
          outbox.actor_id, outbox.payload::text AS payload,
          outbox.attempt_count, outbox.max_attempts, outbox.lock_owner,
          outbox.lock_expires_at
""".strip()

ACK_SQL = """
UPDATE kernel.outbox_events
SET outbox_status = 'PUBLISHED',
    published_at = clock_timestamp(),
    publish_ack_ref = $4,
    last_error_code = NULL,
    lock_owner = NULL,
    locked_at = NULL,
    lock_expires_at = NULL,
    updated_at = clock_timestamp()
WHERE event_id = $1
  AND organization_id = $2
  AND outbox_status IN ('COMMITTED', 'RETRY_PENDING')
  AND lock_owner = $3
  AND lock_expires_at > clock_timestamp()
  AND published_at IS NULL
""".strip()

FAIL_SQL = """
UPDATE kernel.outbox_events
SET outbox_status = CASE
        WHEN attempt_count >= max_attempts THEN 'DEAD_LETTER'
        ELSE 'RETRY_PENDING'
    END,
    next_attempt_at = CASE
        WHEN attempt_count >= max_attempts THEN next_attempt_at
        ELSE clock_timestamp() + make_interval(
            secs => LEAST(3600, (2 ^ GREATEST(attempt_count - 1, 0)))
        )
    END,
    last_error_code = $4,
    lock_owner = NULL,
    locked_at = NULL,
    lock_expires_at = NULL,
    updated_at = clock_timestamp()
WHERE event_id = $1
  AND organization_id = $2
  AND outbox_status IN ('COMMITTED', 'RETRY_PENDING')
  AND lock_owner = $3
  AND lock_expires_at > clock_timestamp()
  AND published_at IS NULL
""".strip()


def retry_delay_seconds(attempt_count: int) -> int:
    if attempt_count < 1:
        raise OutboxWorkerError("attempt_count must be >= 1")
    exponent = max(attempt_count - 1, 0)
    return min(3600, 1 << exponent)


def _text(row: Mapping[str, RowValue], name: str) -> str:
    value = row.get(name)
    if not isinstance(value, str) or not value.strip():
        raise OutboxWorkerError(f"claimed row field {name} is invalid")
    return value


def _optional_text(row: Mapping[str, RowValue], name: str) -> str | None:
    value = row.get(name)
    if value is not None and not isinstance(value, str):
        raise OutboxWorkerError(f"claimed row field {name} is invalid")
    return value


def _integer(row: Mapping[str, RowValue], name: str) -> int:
    value = row.get(name)
    if not isinstance(value, int):
        raise OutboxWorkerError(f"claimed row field {name} is invalid")
    return value


def _timestamp(row: Mapping[str, RowValue], name: str) -> datetime:
    value = row.get(name)
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise OutboxWorkerError(f"claimed row field {name} is invalid")
    return value


def _claimed(row: Mapping[str, RowValue]) -> ClaimedOutboxEvent:
    attempt_count = _integer(row, "attempt_count")
    max_attempts = _integer(row, "max_attempts")
    if attempt_count < 1 or max_attempts < 1 or attempt_count > max_attempts:
        raise OutboxWorkerError("claimed row attempt bounds are invalid")
    return ClaimedOutboxEvent(
        event_id=_text(row, "event_id"),
        organization_id=_text(row, "organization_id"),
        workspace_id=_optional_text(row, "workspace_id"),
        project_id=_optional_text(row, "project_id"),
        environment_id=_optional_text(row, "environment_id"),
        event_type=_text(row, "event_type"),
        event_version=_text(row, "event_version"),
        correlation_id=_text(row, "correlation_id"),
        actor_type=_text(row, "actor_type"),
        actor_id=_text(row, "actor_id"),
        payload=_text(row, "payload"),
        attempt_count=attempt_count,
        max_attempts=max_attempts,
        lock_owner=_text(row, "lock_owner"),
        lock_expires_at=_timestamp(row, "lock_expires_at"),
    )


@dataclass(frozen=True, slots=True)
class PostgresOutboxWorker:
    connection: OutboxConnection

    def claim(
        self,
        *,
        worker_id: str,
        organization_id: str,
        lease_seconds: int = 60,
        limit: int = 10,
    ) -> tuple[ClaimedOutboxEvent, ...]:
        if not worker_id.strip() or not organization_id.strip():
            raise OutboxWorkerError("worker_id and organization_id are required")
        if lease_seconds < 1 or limit < 1:
            raise OutboxWorkerError("lease_seconds and limit must be >= 1")
        with self.connection.cursor() as cursor:
            cursor.execute(
                CLAIM_SQL,
                (worker_id, lease_seconds, organization_id, limit),
            )
            claimed = tuple(_claimed(row) for row in cursor.fetchall())
        self.connection.commit()
        return claimed

    def acknowledge(self, *, event_id: str, organization_id: str, worker_id: str, publish_ack_ref: str) -> None:
        if not publish_ack_ref.strip():
            raise OutboxWorkerError("publish_ack_ref must not be empty")
        self._transition(
            ACK_SQL,
            (event_id, organization_id, worker_id, publish_ack_ref),
        )

    def fail(self, *, event_id: str, organization_id: str, worker_id: str, error_code: str) -> None:
        if not error_code.strip():
            raise OutboxWorkerError("error_code must not be empty")
        self._transition(FAIL_SQL, (event_id, organization_id, worker_id, error_code))

    def _transition(self, statement: str, parameters: tuple[RowValue, ...]) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(statement, parameters)
            if cursor.rowcount != 1:
                self.connection.rollback()
                raise OutboxWorkerError(
                    "outbox transition rejected: lease or tenant scope is invalid"
                )
        self.connection.commit()


def lease_expiry(*, now: datetime, lease_seconds: int) -> datetime:
    if now.tzinfo is None or lease_seconds < 1:
        raise OutboxWorkerError("now must be timezone-aware and lease_seconds >= 1")
    return now + timedelta(seconds=lease_seconds)
