#!/usr/bin/env python3
from __future__ import annotations

"""
Phase 8 outbox processing observability validator.

Validates that:
- kernel/outbox/processor.py accepts an OutboxEventLogEmitter and emits
  correct events through the processing loop
- delivery_published is emitted only on successful ack
- retry_scheduled is emitted only when max_attempts is NOT exhausted
- dead_letter is emitted only when max_attempts IS exhausted
- dead_letter is terminal (no retry_scheduled for the same exhausted event)
- observability payloads do not leak full event payload or secret-bearing fields
- the processor runs without crashing when the emitter is None
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from datetime import datetime, timezone
from unittest.mock import MagicMock

from kernel.outbox.runtime import ClaimedOutboxEvent
from kernel.outbox.processor import (
    DeliveryAcknowledgement,
    DeliveryFailure,
    DeliveryOutcome,
    OutboxLeaseStore,
    OutboxProcessor,
    ProcessingSettings,
)
from kernel.outbox.observability import (
    OutboxEventLogFact,
    OutboxObservabilityEmitter,
    InMemoryStructuredLogSink,
)

_SINK = InMemoryStructuredLogSink()


def _make_emitter() -> OutboxObservabilityEmitter:
    return FakeEmitter(_SINK)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _event(
    *,
    event_id: str = "evt-001",
    attempt_count: int = 1,
    lock_expires_at: datetime | None = None,
) -> ClaimedOutboxEvent:
    return ClaimedOutboxEvent(
        event_id=event_id,
        organization_id="o-1",
        workspace_id="ws-1",
        project_id="p-1",
        environment_id="e-1",
        event_type="webhook.dispatch.v1",
        event_version="1",
        correlation_id="corr-1",
        actor_type="webhook",
        actor_id="wh-1",
        payload="{}",
        attempt_count=attempt_count,
        max_attempts=5,
        lock_owner="worker-1",
        lock_expires_at=lock_expires_at or datetime.now(timezone.utc),
    )


errors: list[str] = []


def _add(msg: str) -> None:
    errors.append(msg)


class FakeEmitter(OutboxObservabilityEmitter):
    def __init__(self, sink: InMemoryStructuredLogSink) -> None:
        super().__init__(
            sink=sink,
            correlation_id="corr-fake",
            organization_id="o-fake",
            worker_id="w-fake",
            lease_seconds=60,
        )
        self.records: list[dict] = []

    def emit_claimed(self, *, fact: OutboxEventLogFact, worker_id: str | None = None) -> dict:
        self.records.append({"kind": "claimed", "fact": fact})
        return {}

    def emit_lease_refreshed(self, *, fact: OutboxEventLogFact) -> dict:
        return {}

    def emit_lease_released(self, *, fact: OutboxEventLogFact) -> dict:
        return {}

    def emit_claim_rejected(self, *, reason: str, fact: OutboxEventLogFact | None = None) -> dict:
        return {}

    def emit_delivery_published(
        self,
        *,
        fact: OutboxEventLogFact,
        published_at: str | None = None,
    ) -> dict:
        self.records.append({"kind": "published", "fact": fact, "published_at": published_at})
        return {}

    def emit_retry_scheduled(
        self,
        *,
        fact: OutboxEventLogFact,
        error_code: str,
        next_attempt_at: str,
    ) -> dict:
        self.records.append({
            "kind": "retry_scheduled",
            "fact": fact,
            "error_code": error_code,
            "next_attempt_at": next_attempt_at,
        })
        return {}

    def emit_dead_letter(
        self,
        *,
        fact: OutboxEventLogFact,
        error_code: str,
    ) -> dict:
        self.records.append({"kind": "dead_letter", "fact": fact, "error_code": error_code})
        return {}


class FakeStore(OutboxLeaseStore):
    def __init__(self, events: list[ClaimedOutboxEvent] | None = None) -> None:
        self.events = list(events or [])
        self.ack_calls: list[dict[str, str]] = []
        self.fail_calls: list[dict[str, str]] = []

    def claim(
        self,
        *,
        worker_id: str,
        organization_id: str,
        lease_seconds: int,
        limit: int,
    ) -> tuple[ClaimedOutboxEvent, ...]:
        return tuple(self.events[:limit])

    def acknowledge(
        self,
        *,
        event_id: str,
        organization_id: str,
        worker_id: str,
        publish_ack_ref: str,
    ) -> None:
        self.ack_calls.append({
            "event_id": event_id,
            "organization_id": organization_id,
            "worker_id": worker_id,
            "publish_ack_ref": publish_ack_ref,
        })

    def fail(
        self,
        *,
        event_id: str,
        organization_id: str,
        worker_id: str,
        error_code: str,
    ) -> None:
        self.fail_calls.append({
            "event_id": event_id,
            "organization_id": organization_id,
            "worker_id": worker_id,
            "error_code": error_code,
        })


print("=== VALIDATE: processor runs cleanly with emitter=None (no crash) ===")
try:
    settings = ProcessingSettings(worker_id="w1", organization_id="o-1")
    store = FakeStore([])
    adapter = MagicMock(spec=[])  # not used because no events
    proc = OutboxProcessor(store=store, adapter=adapter, settings=settings, emitter=None)
    summary = proc.run_once()
    if summary.claimed != 0 or summary.acknowledged != 0 or summary.failed != 0:
        _add("expected zeroed summary with no events, got: %r" % (summary,))
    else:
        print("OK: processor with emitter=None returns zeroed summary")
except Exception as e:
    _add("processor with emitter=None raised: %r" % (e,))


print("=== VALIDATE: processor emits claim + delivery_published on success ===")
try:
    settings = ProcessingSettings(worker_id="w-a", organization_id="o-1")
    store = FakeStore([_event(event_id="evt-pub-1")])
    ack = DeliveryAcknowledgement(publish_ack_ref="pub-ack-xyz")
    adapter = MagicMock()
    adapter.publish.return_value = ack
    emitter = _make_emitter()
    proc = OutboxProcessor(store=store, adapter=adapter, settings=settings, emitter=emitter)
    summary = proc.run_once()

    if summary.claimed != 1 or summary.acknowledged != 1 or summary.failed != 0:
        _add("expected 1 claimed / 1 acknowledged / 0 failed, got: %r" % (summary,))
    records = emitter.records
    kinds = [r["kind"] for r in records]
    if kinds != ["claimed", "published"]:
        _add("expected []claimed, published], got: %r" % (kinds,))

    published = records[-1]
    fact = published["fact"]
    if not isinstance(fact, OutboxEventLogFact):
        _add("published fact is not OutboxEventLogFact: %r" % (type(fact),))
    else:
        if fact.event_id != "evt-pub-1":
            _add("published fact event_id mismatch: %r" % (fact.event_id,))
        if fact.delivery_id != "pub-ack-xyz":
            _add("published fact delivery_id should equal ack ref: %r" % (fact.delivery_id,))
        if fact.error_code is not None:
            _add("published fact must have null error_code, got: %r" % (fact.error_code,))
        # Do not leak full payload
        if getattr(fact, "payload", None) is not None:
            _add("OutboxEventLogFact should not carry raw payload; found payload field")

    if published.get("published_at") != "pub-ack-xyz":
        _add("published_at should equal ack ref: %r" % (published.get("published_at"),))

    # ack calls stored durably
    if len(store.ack_calls) != 1:
        _add("expected 1 ack call, got: %r" % (store.ack_calls,))
    elif store.ack_calls[0]["event_id"] != "evt-pub-1":
        _add("ack call event_id mismatch: %r" % (store.ack_calls[0],))
    elif store.ack_calls[0]["publish_ack_ref"] != "pub-ack-xyz":
        _add("ack publish_ack_ref mismatch: %r" % (store.ack_calls[0],))
    else:
        print("OK: success path emits claim then delivery_published with correct ack ref")
except Exception as e:
    _add("success path raised: %r" % (e,))


print("=== VALIDATE: failure below max_attempts emits retry_scheduled ===")
try:
    settings = ProcessingSettings(worker_id="w-b", organization_id="o-1", batch_size=2)
    store = FakeStore([
        _event(event_id="evt-pub-2"),
        _event(event_id="evt-retry-1", attempt_count=2),
    ])
    adapter = MagicMock()
    adapter.publish.side_effect = [
        DeliveryAcknowledgement(publish_ack_ref="pub-ack-2"),
        DeliveryFailure(error_code="webhook.timeout"),
    ]
    emitter = _make_emitter()
    proc = OutboxProcessor(store=store, adapter=adapter, settings=settings, emitter=emitter)
    summary = proc.run_once()

    if summary.claimed != 2 or summary.acknowledged != 1 or summary.failed != 1:
        _add("expected 2 claimed / 1 acknowledged / 1 failed, got: %r" % (summary,))

    kinds = [r["kind"] for r in emitter.records]
    if kinds != ["claimed", "published", "claimed", "retry_scheduled"]:
        _add("expected []claimed, published, claimed, retry_scheduled], got: %r" % (kinds,))

    retry = next(r for r in emitter.records if r["kind"] == "retry_scheduled")
    fact = retry["fact"]
    if fact.event_id != "evt-retry-1":
        _add("retry fact event_id mismatch: %r" % (fact.event_id,))
    if fact.attempt_count != 2:
        _add("retry fact attempt_count mismatch: %r" % (fact.attempt_count,))
    if fact.error_code != "webhook.timeout":
        _add("retry fact error_code mismatch: %r" % (fact.error_code,))
    if retry["error_code"] != "webhook.timeout":
        _add("emitted retry error_code mismatch: %r" % (retry["error_code"],))

    # Durable fail recorded
    if len(store.fail_calls) != 1:
        _add("expected 1 fail call, got: %r" % (store.fail_calls,))
    elif store.fail_calls[0]["event_id"] != "evt-retry-1":
        _add("fail event_id mismatch: %r" % (store.fail_calls[0],))
    elif store.fail_calls[0]["error_code"] != "webhook.timeout":
        _add("fail error_code mismatch: %r" % (store.fail_calls[0],))
    else:
        print("OK: failure below max emits retry_scheduled with error_code")
except Exception as e:
    _add("retry path raised: %r" % (e,))


print("=== VALIDATE: exhausted event emits dead_letter and fails durably ===")
try:
    settings = ProcessingSettings(worker_id="w-c", organization_id="o-1", batch_size=1)
    the_event = _event(event_id="evt-dead-1", attempt_count=5, lock_expires_at=datetime(2026, 9, 9, 12, 0, 0, tzinfo=timezone.utc))
    store = FakeStore([the_event])
    adapter = MagicMock()
    adapter.publish.return_value = DeliveryFailure(error_code="webhook.dead")
    emitter = _make_emitter()
    proc = OutboxProcessor(store=store, adapter=adapter, settings=settings, emitter=emitter)
    summary = proc.run_once()

    if summary.claimed != 1 or summary.acknowledged != 0 or summary.failed != 1:
        _add("expected 1 claimed / 0 acknowledged / 1 failed, got: %r" % (summary,))

    kinds = [r["kind"] for r in emitter.records]
    if kinds != ["claimed", "dead_letter"]:
        _add("expected []claimed, dead_letter], got: %r" % (kinds,))

    dead = emitter.records[-1]
    fact = dead["fact"]
    if fact.event_id != "evt-dead-1":
        _add("dead_letter fact event_id mismatch: %r" % (fact.event_id,))
    if fact.error_code != "webhook.dead":
        _add("dead_letter fact error_code mismatch: %r" % (fact.error_code,))
    if dead["error_code"] != "webhook.dead":
        _add("emitted dead_letter error_code mismatch: %r" % (dead["error_code"],))

    # Durable fail recorded
    if len(store.fail_calls) != 1:
        _add("expected 1 fail call, got: %r" % (store.fail_calls,))
    elif store.fail_calls[0]["event_id"] != "evt-dead-1":
        _add("fail event_id mismatch: %r" % (store.fail_calls[0],))
    elif store.fail_calls[0]["error_code"] != "webhook.dead":
        _add("fail error_code mismatch: %r" % (store.fail_calls[0],))
    else:
        print("OK: exhausted event emits dead_letter and durable fail")
except Exception as e:
    _add("exhausted path raised: %r" % (e,))


print("=== VALIDATE: dead_letter is terminal (no retry_scheduled for exhausted event) ===")
try:
    settings = ProcessingSettings(worker_id="w-d", organization_id="o-1", batch_size=1)
    the_event = _event(event_id="evt-terminal-1", attempt_count=5, lock_expires_at=datetime(2026, 9, 9, 12, 0, 0, tzinfo=timezone.utc))
    store = FakeStore([the_event])
    adapter = MagicMock()
    adapter.publish.return_value = DeliveryFailure(error_code="webhook.terminator")
    emitter = _make_emitter()
    proc = OutboxProcessor(store=store, adapter=adapter, settings=settings, emitter=emitter)
    proc.run_once()

    kinds = [r["kind"] for r in emitter.records]
    if "retry_scheduled" in kinds:
        _add("terminal invariant violated: retry_scheduled emitted for exhausted event, got kinds: %r" % (kinds,))
    if kinds != ["claimed", "dead_letter"]:
        _add("expected exactly []claimed, dead_letter] for exhausted event, got: %r" % (kinds,))
    else:
        print("OK: dead_letter terminal invariant held (no retry_scheduled for exhausted event)")
except Exception as e:
    _add("terminal invariant scenario raised: %r" % (e,))


print("=== VALIDATE: observability payload does not leak full event payload ===")
try:
    settings = ProcessingSettings(worker_id="w-leak", organization_id="o-1", batch_size=1)
    store = FakeStore([_event(event_id="evt-leak-1")])
    ack = DeliveryAcknowledgement(publish_ack_ref="pub-leak-ack")
    adapter = MagicMock()
    adapter.publish.return_value = ack
    emitter = _make_emitter()
    proc = OutboxProcessor(store=store, adapter=adapter, settings=settings, emitter=emitter)
    proc.run_once()

    sensitive_terms = ("secret", "token", "api_key", "password", "nopassword")
    for record in emitter.records:
        payload = repr(record)
        lowered = payload.lower()
        for term in sensitive_terms:
            if term in lowered:
                _add("observability record leaked sensitive term %r in %r" % (term, payload))

    # Ensure the emitted fact does not carry the raw event payload
    for record in emitter.records:
        fact = record.get("fact")
        if isinstance(fact, OutboxEventLogFact):
            if hasattr(fact, "payload"):
                _add("OutboxEventLogFact should not expose raw payload attribute; found payload on %r" % (fact,))
        else:
            _add("expected OutboxEventLogFact in record, got: %r" % (type(fact),))

    print("OK: observability events do not carry full payload or secret-bearing fields")
except Exception as e:
    _add("payload leak scenario raised: %r" % (e,))


if errors:
    for e in errors:
        print("ERROR:", e)
    sys.exit(1)

print("\nAll phase8 outbox processing observability assertions passed.")
