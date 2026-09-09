from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, assert_never
from typing import Any

from kernel.outbox.runtime import ClaimedOutboxEvent
from kernel.outbox.rate_limit import (
    OutboxRateLimiter,
    RateLimitOutcome,
    RateLimitAllowance,
)
from kernel.outbox.observability import (
    OutboxEventLogFact,
    OutboxObservabilityEmitter,
)


class ProcessingError(Exception):
    def __init__(self, *, field: str, reason: str) -> None:
        super().__init__(reason)
        self.field = field
        self.reason = reason

    def __str__(self) -> str:
        return f"{self.field}: {self.reason}"


@dataclass(frozen=True, slots=True)
class ProcessingSettings:
    worker_id: str
    organization_id: str
    lease_seconds: int = 60
    batch_size: int = 10
    max_batches: int = 100

    def validate(self) -> None:
        if not self.worker_id.strip():
            raise ProcessingError(field="worker_id", reason="must not be empty")
        if not self.organization_id.strip():
            raise ProcessingError(field="organization_id", reason="must not be empty")
        if self.lease_seconds < 1:
            raise ProcessingError(field="lease_seconds", reason="must be >= 1")
        if self.batch_size < 1:
            raise ProcessingError(field="batch_size", reason="must be >= 1")
        if self.max_batches < 1:
            raise ProcessingError(field="max_batches", reason="must be >= 1")


@dataclass(frozen=True, slots=True)
class DeliveryAcknowledgement:
    publish_ack_ref: str

    def validate(self) -> None:
        if not self.publish_ack_ref.strip():
            raise ProcessingError(field="publish_ack_ref", reason="must not be empty")


@dataclass(frozen=True, slots=True)
class DeliveryFailure:
    error_code: str

    def validate(self) -> None:
        if not self.error_code.strip():
            raise ProcessingError(field="error_code", reason="must not be empty")


DeliveryOutcome = DeliveryAcknowledgement | DeliveryFailure


class DeliveryAdapter(Protocol):
    def publish(self, event: ClaimedOutboxEvent) -> DeliveryOutcome: ...


class OutboxLeaseStore(Protocol):
    def claim(
        self,
        *,
        worker_id: str,
        organization_id: str,
        lease_seconds: int,
        limit: int,
    ) -> tuple[ClaimedOutboxEvent, ...]: ...

    def acknowledge(
        self,
        *,
        event_id: str,
        organization_id: str,
        worker_id: str,
        publish_ack_ref: str,
    ) -> None: ...

    def fail(
        self,
        *,
        event_id: str,
        organization_id: str,
        worker_id: str,
        error_code: str,
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class ProcessingSummary:
    claimed: int
    acknowledged: int
    failed: int


@dataclass(frozen=True, slots=True)
class ProcessingLoopSummary:
    batches: int
    claimed: int
    acknowledged: int
    failed: int
    drained: bool


@dataclass(frozen=True, slots=True)
class OutboxProcessor:
    store: OutboxLeaseStore
    adapter: DeliveryAdapter
    settings: ProcessingSettings
    rate_limiter: OutboxRateLimiter | None = None
    emitter: OutboxObservabilityEmitter | None = None

    def run_once(self) -> ProcessingSummary:
        self.settings.validate()
        events = self.store.claim(
            worker_id=self.settings.worker_id,
            organization_id=self.settings.organization_id,
            lease_seconds=self.settings.lease_seconds,
            limit=self.settings.batch_size,
        )
        acknowledged = 0
        failed = 0

        for event in events:
            if event.organization_id != self.settings.organization_id:
                raise ProcessingError(
                    field="organization_id",
                    reason="claimed event is outside the worker tenant scope",
                )
            self._emit_claimed(event)
            rate_outcome = self._check_rate(event)
            if not rate_outcome.allowed:
                continue
            outcome = self.adapter.publish(event)
            if isinstance(outcome, DeliveryAcknowledgement):
                outcome.validate()
                self.store.acknowledge(
                    event_id=event.event_id,
                    organization_id=event.organization_id,
                    worker_id=self.settings.worker_id,
                    publish_ack_ref=outcome.publish_ack_ref,
                )
                self._emit_published(event, publish_ack_ref=outcome.publish_ack_ref)
                acknowledged += 1
            else:
                outcome.validate()
                self.store.fail(
                    event_id=event.event_id,
                    organization_id=event.organization_id,
                    worker_id=self.settings.worker_id,
                    error_code=outcome.error_code,
                )
                self._emit_outcome(event, error_code=outcome.error_code)
                failed += 1

        return ProcessingSummary(
            claimed=len(events),
            acknowledged=acknowledged,
            failed=failed,
        )

    def run_until_idle(self) -> ProcessingLoopSummary:
        batches = 0
        claimed = 0
        acknowledged = 0
        failed = 0

        for _ in range(self.settings.max_batches):
            summary = self.run_once()
            if summary.claimed == 0:
                return ProcessingLoopSummary(
                    batches=batches,
                    claimed=claimed,
                    acknowledged=acknowledged,
                    failed=failed,
                    drained=True,
                )
            batches += 1
            claimed += summary.claimed
            acknowledged += summary.acknowledged
            failed += summary.failed

        return ProcessingLoopSummary(
            batches=batches,
            claimed=claimed,
            acknowledged=acknowledged,
            failed=failed,
            drained=False,
        )

    def _emit_claimed(self, event: ClaimedOutboxEvent) -> None:
        if self.emitter is None:
            return
        fact = OutboxEventLogFact(
            event_id=event.event_id,
            organization_id=event.organization_id,
            workspace_id=event.workspace_id,
            project_id=event.project_id,
            environment_id=event.environment_id,
            event_type=event.event_type,
            event_version=event.event_version,
            correlation_id=event.correlation_id,
            resource_type=event.event_type,
            resource_id=event.actor_id,
            attempt_count=event.attempt_count,
            max_attempts=event.max_attempts,
            subscription_id=None,
            delivery_id=None,
            error_code=None,
            next_attempt_at=None,
            lock_owner=event.lock_owner,
            lock_expires_at=event.lock_expires_at.isoformat(),
        )
        self.emitter.emit_claimed(fact=fact)

    def _emit_published(
        self,
        event: ClaimedOutboxEvent,
        *,
        publish_ack_ref: str,
    ) -> None:
        if self.emitter is None:
            return
        fact = OutboxEventLogFact(
            event_id=event.event_id,
            organization_id=event.organization_id,
            workspace_id=event.workspace_id,
            project_id=event.project_id,
            environment_id=event.environment_id,
            event_type=event.event_type,
            event_version=event.event_version,
            correlation_id=event.correlation_id,
            resource_type=event.event_type,
            resource_id=event.actor_id,
            attempt_count=event.attempt_count,
            max_attempts=event.max_attempts,
            subscription_id=None,
            delivery_id=publish_ack_ref,
            error_code=None,
            next_attempt_at=None,
            lock_owner=event.lock_owner,
            lock_expires_at=event.lock_expires_at.isoformat(),
        )
        self.emitter.emit_delivery_published(
            fact=fact,
            published_at=publish_ack_ref,
        )

    def _emit_outcome(
        self,
        event: ClaimedOutboxEvent,
        *,
        error_code: str,
    ) -> None:
        if self.emitter is None:
            return
        if event.attempt_count >= event.max_attempts:
            fact = OutboxEventLogFact(
                event_id=event.event_id,
                organization_id=event.organization_id,
                workspace_id=event.workspace_id,
                project_id=event.project_id,
                environment_id=event.environment_id,
                event_type=event.event_type,
                event_version=event.event_version,
                correlation_id=event.correlation_id,
                resource_type=event.event_type,
                resource_id=event.actor_id,
                attempt_count=event.attempt_count,
                max_attempts=event.max_attempts,
                subscription_id=None,
                delivery_id=None,
                error_code=error_code,
                next_attempt_at=None,
                lock_owner=event.lock_owner,
                lock_expires_at=event.lock_expires_at.isoformat(),
            )
            self.emitter.emit_dead_letter(fact=fact, error_code=error_code)
        else:
            from datetime import datetime, timezone

            next_attempt_at = datetime.now(timezone.utc).isoformat()
            fact = OutboxEventLogFact(
                event_id=event.event_id,
                organization_id=event.organization_id,
                workspace_id=event.workspace_id,
                project_id=event.project_id,
                environment_id=event.environment_id,
                event_type=event.event_type,
                event_version=event.event_version,
                correlation_id=event.correlation_id,
                resource_type=event.event_type,
                resource_id=event.actor_id,
                attempt_count=event.attempt_count,
                max_attempts=event.max_attempts,
                subscription_id=None,
                delivery_id=None,
                error_code=error_code,
                next_attempt_at=next_attempt_at,
                lock_owner=event.lock_owner,
                lock_expires_at=event.lock_expires_at.isoformat(),
            )
            self.emitter.emit_retry_scheduled(
                fact=fact,
                error_code=error_code,
                next_attempt_at=next_attempt_at,
            )

    def _check_rate(self, event: ClaimedOutboxEvent) -> RateLimitOutcome:
        if self.rate_limiter is None:
            return RateLimitAllowance(
                allowed=True,
                remaining=-1,
                retry_after_seconds=None,
                evaluated_at="",
            )
        return self.rate_limiter.check(
            worker_id=self.settings.worker_id,
            organization_id=event.organization_id,
            event_id=event.event_id,
            attempt_count=event.attempt_count,
        )
