#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kernel.outbox.processor import (
    DeliveryAcknowledgement,
    DeliveryFailure,
    OutboxProcessor,
    ProcessingError,
    ProcessingSettings,
)
from kernel.outbox.runtime import ClaimedOutboxEvent


def claimed(
    event_id: str,
    correlation_id: str,
    organization_id: str = "org-processing",
) -> ClaimedOutboxEvent:
    return ClaimedOutboxEvent(
        event_id=event_id,
        organization_id=organization_id,
        workspace_id="ws-processing",
        project_id="proj-processing",
        environment_id="env-processing",
        event_type="order.created",
        event_version="1",
        correlation_id=correlation_id,
        actor_type="SYSTEM",
        actor_id="processing-validation",
        payload='{"status":"CREATED"}',
        attempt_count=1,
        max_attempts=3,
        lock_owner="worker-processing",
        lock_expires_at=datetime(2026, 9, 9, 18, 0, tzinfo=timezone.utc),
    )


class FakeLeaseStore:
    def __init__(self, events: tuple[ClaimedOutboxEvent, ...]) -> None:
        self.events: tuple[ClaimedOutboxEvent, ...] = events
        self.acknowledgements: list[tuple[str, str]] = []
        self.failures: list[tuple[str, str]] = []

    def claim(self, *, worker_id: str, organization_id: str, lease_seconds: int, limit: int) -> tuple[ClaimedOutboxEvent, ...]:
        if worker_id != "worker-processing" or organization_id != "org-processing":
            raise AssertionError("processing claim scope changed")
        if lease_seconds != 30 or limit != 10:
            raise AssertionError("processing lease settings changed")
        events = self.events
        self.events = ()
        return events

    def acknowledge(self, *, event_id: str, organization_id: str, worker_id: str, publish_ack_ref: str) -> None:
        if organization_id != "org-processing" or worker_id != "worker-processing":
            raise AssertionError("acknowledgement scope changed")
        self.acknowledgements.append((event_id, publish_ack_ref))

    def fail(self, *, event_id: str, organization_id: str, worker_id: str, error_code: str) -> None:
        if organization_id != "org-processing" or worker_id != "worker-processing":
            raise AssertionError("failure scope changed")
        self.failures.append((event_id, error_code))


class FakeDeliveryAdapter:
    def __init__(self) -> None:
        self.seen_context: list[tuple[str, str, str]] = []

    def publish(self, event: ClaimedOutboxEvent) -> DeliveryAcknowledgement | DeliveryFailure:
        self.seen_context.append(
            (event.organization_id, event.correlation_id, event.event_id)
        )
        if event.event_id == "evt-success":
            return DeliveryAcknowledgement(publish_ack_ref="ack://provider/evt-success")
        return DeliveryFailure(error_code="PROVIDER_TIMEOUT")


store = FakeLeaseStore(
    (
        claimed("evt-success", "corr-success"),
        claimed("evt-failure", "corr-failure"),
    )
)
adapter = FakeDeliveryAdapter()
processor = OutboxProcessor(
    store=store,
    adapter=adapter,
    settings=ProcessingSettings(
        worker_id="worker-processing",
        organization_id="org-processing",
        lease_seconds=30,
        batch_size=10,
        max_batches=3,
    ),
)

summary = processor.run_until_idle()

if summary.batches != 1 or summary.claimed != 2 or summary.acknowledged != 1 or summary.failed != 1 or not summary.drained:
    raise SystemExit("ERROR: processing summary is invalid")
if store.acknowledgements != [("evt-success", "ack://provider/evt-success")]:
    raise SystemExit("ERROR: successful delivery acknowledgement was not persisted")
if store.failures != [("evt-failure", "PROVIDER_TIMEOUT")]:
    raise SystemExit("ERROR: failed delivery was not scheduled through Kernel state")
if adapter.seen_context != [
    ("org-processing", "corr-success", "evt-success"),
    ("org-processing", "corr-failure", "evt-failure"),
]:
    raise SystemExit("ERROR: adapter handoff lost tenant or correlation context")

cross_tenant_store = FakeLeaseStore(
    (claimed("evt-cross", "corr-cross", "org-other"),)
)
cross_tenant_adapter = FakeDeliveryAdapter()
try:
    _ = OutboxProcessor(
        store=cross_tenant_store,
        adapter=cross_tenant_adapter,
        settings=processor.settings,
    ).run_once()
except ProcessingError as error:
    cross_tenant_rejected = error.field == "organization_id"
else:
    cross_tenant_rejected = False
if not cross_tenant_rejected or cross_tenant_adapter.seen_context:
    raise SystemExit("ERROR: cross-tenant claimed event reached the adapter")

print("OK: worker processing claims a bounded batch")
print("OK: delivery adapter receives tenant and correlation context")
print("OK: provider acknowledgement reference is persisted")
print("OK: adapter failure returns to Kernel retry authority")
print("OK: cross-tenant claimed event fails closed before adapter handoff")
print("STATUS: PHASE 8 OUTBOX PROCESSING LOOP READY")
