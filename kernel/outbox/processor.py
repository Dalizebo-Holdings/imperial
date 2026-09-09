from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, assert_never, override

from kernel.outbox.runtime import ClaimedOutboxEvent


@dataclass(frozen=True, slots=True)
class ProcessingError(Exception):
    field: str
    reason: str

    @override
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
            raise ProcessingError("worker_id", "must not be empty")
        if not self.organization_id.strip():
            raise ProcessingError("organization_id", "must not be empty")
        if self.lease_seconds < 1:
            raise ProcessingError("lease_seconds", "must be >= 1")
        if self.batch_size < 1:
            raise ProcessingError("batch_size", "must be >= 1")
        if self.max_batches < 1:
            raise ProcessingError("max_batches", "must be >= 1")


@dataclass(frozen=True, slots=True)
class DeliveryAcknowledgement:
    publish_ack_ref: str

    def validate(self) -> None:
        if not self.publish_ack_ref.strip():
            raise ProcessingError("publish_ack_ref", "must not be empty")


@dataclass(frozen=True, slots=True)
class DeliveryFailure:
    error_code: str

    def validate(self) -> None:
        if not self.error_code.strip():
            raise ProcessingError("error_code", "must not be empty")


type DeliveryOutcome = DeliveryAcknowledgement | DeliveryFailure


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
                    "organization_id",
                    "claimed event is outside the worker tenant scope",
                )
            outcome = self.adapter.publish(event)
            match outcome:
                case DeliveryAcknowledgement(publish_ack_ref=publish_ack_ref):
                    outcome.validate()
                    self.store.acknowledge(
                        event_id=event.event_id,
                        organization_id=event.organization_id,
                        worker_id=self.settings.worker_id,
                        publish_ack_ref=publish_ack_ref,
                    )
                    acknowledged += 1
                case DeliveryFailure(error_code=error_code):
                    outcome.validate()
                    self.store.fail(
                        event_id=event.event_id,
                        organization_id=event.organization_id,
                        worker_id=self.settings.worker_id,
                        error_code=error_code,
                    )
                    failed += 1
                case _ as unreachable:
                    assert_never(unreachable)

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
