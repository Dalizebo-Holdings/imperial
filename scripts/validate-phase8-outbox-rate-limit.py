#!/usr/bin/env python3
from __future__ import annotations

"""
Phase 8 outbox delivery rate-limit envelope validator.

Validates that:
- kernel/outbox/rate_limit exposes a concrete TokenBucketRateLimiter
- the processor accepts an optional rate limiter and honors denials
- denied deliveries are skipped without ack/fail or outcome emission
- invalid ids/attempt counts are rejected
- token bucket capacity is bounded and refill-based
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from datetime import datetime, timezone

from kernel.outbox.runtime import ClaimedOutboxEvent
from kernel.outbox.processor import (
    DeliveryAcknowledgement,
    DeliveryFailure,
    OutboxLeaseStore,
    OutboxProcessor,
    ProcessingSettings,
)
from kernel.outbox.rate_limit import (
    TokenBucketRateLimiter,
    OutboxRateLimitError,
)

errors: list[str] = []


def _add(msg: str) -> None:
    errors.append(msg)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _event(*, event_id: str = "evt-001", attempt_count: int = 1) -> ClaimedOutboxEvent:
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
        lock_expires_at=datetime.now(timezone.utc),
    )


class AckOnlyStore(OutboxLeaseStore):
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
        self.ack_calls.append({"event_id": event_id, "publish_ack_ref": publish_ack_ref})

    def fail(
        self,
        *,
        event_id: str,
        organization_id: str,
        worker_id: str,
        error_code: str,
    ) -> None:
        self.fail_calls.append({"event_id": event_id, "error_code": error_code})


class _FakeAdapter:
    def __init__(self, outcomes: list) -> None:
        self.outcomes = list(outcomes)
        self.publish_calls: list[ClaimedOutboxEvent] = []

    def publish(self, event: ClaimedOutboxEvent):
        self.publish_calls.append(event)
        if not self.outcomes:
            return DeliveryAcknowledgement(publish_ack_ref=_iso_now())
        return self.outcomes.pop(0)


class _NoopEmitter:
    def emit_claimed(self, *, fact) -> dict:
        return {}

    def emit_lease_refreshed(self, *, fact) -> dict:
        return {}

    def emit_lease_released(self, *, fact) -> dict:
        return {}

    def emit_claim_rejected(self, *, reason, fact=None) -> dict:
        return {}

    def emit_delivery_published(self, *, fact, published_at=None) -> dict:
        return {}

    def emit_retry_scheduled(self, *, fact, error_code, next_attempt_at) -> dict:
        return {}

    def emit_dead_letter(self, *, fact, error_code) -> dict:
        return {}


print("=== VALIDATE: TokenBucketRateLimiter rejects invalid input ===")
try:
    limiter = TokenBucketRateLimiter(capacity=1, refill_seconds=1, max_wait_seconds=0)
    bad_calls = [
        dict(worker_id="", organization_id="o1", event_id="e1", attempt_count=1),
        dict(worker_id="w1", organization_id="", event_id="e1", attempt_count=1),
        dict(worker_id="w1", organization_id="o1", event_id="", attempt_count=1),
        dict(worker_id="w1", organization_id="o1", event_id="e1", attempt_count=0),
        dict(worker_id="w1", organization_id="o1", event_id="e1", attempt_count=-1),
    ]
    for kwargs in bad_calls:
        try:
            limiter.check(**kwargs)
            _add("expected OutboxRateLimitError for %r" % (kwargs,))
        except OutboxRateLimitError:
            pass
    print("OK: rate limiter fails closed on invalid ids / attempt counts")
except Exception as e:
    _add("rate limit rejection validation raised: %r" % (e,))


print("=== VALIDATE: bounded capacity semantics ===")
try:
    limiter = TokenBucketRateLimiter(capacity=2, refill_seconds=60, max_wait_seconds=0, now=datetime(2026, 9, 9, 12, 0, 0, tzinfo=timezone.utc))
    assert limiter.check(worker_id="w1", organization_id="o1", event_id="e1", attempt_count=1).allowed is True
    assert limiter.check(worker_id="w1", organization_id="o1", event_id="e2", attempt_count=1).allowed is True
    denied = limiter.check(worker_id="w1", organization_id="o1", event_id="e3", attempt_count=1)
    assert denied.allowed is False
    assert denied.remaining == 0
    assert denied.retry_after_seconds is not None and denied.retry_after_seconds > 0
    print("OK: token bucket denies when capacity exhausted and reports retry-after")
except Exception as e:
    _add("bounded capacity validation raised: %r" % (e,))


print("=== VALIDATE: denied rate limit skips delivery but does not ack/fail nor emit delivery outcomes ===")
try:
    store = AckOnlyStore([_event(event_id="evt-ok"), _event(event_id="evt-denied")])
    limiter = TokenBucketRateLimiter(capacity=1, refill_seconds=120, max_wait_seconds=0, now=datetime(2026, 9, 9, 12, 0, 0, tzinfo=timezone.utc))
    ack = DeliveryAcknowledgement(publish_ack_ref="ack-ok")
    adapter = _FakeAdapter([ack, DeliveryFailure(error_code="webhook.should_not_fire")])
    emitter = _NoopEmitter()
    proc = OutboxProcessor(
        store=store,
        adapter=adapter,
        settings=ProcessingSettings(worker_id="w-rl", organization_id="o-1", batch_size=2),
        rate_limiter=limiter,
        emitter=emitter,
    )
    summary = proc.run_once()

    if summary.claimed != 2 or summary.acknowledged != 1 or summary.failed != 0:
        _add("expected 2 claimed / 1 acknowledged / 0 failed, got: %r" % (summary,))

    if len(store.ack_calls) != 1:
        _add("expected exactly 1 durable ack, got: %r" % (store.ack_calls,))
    elif store.ack_calls[0]["event_id"] != "evt-ok":
        _add("expected ack for evt-ok, got: %r" % (store.ack_calls[0],))

    if len(store.fail_calls) != 0:
        _add("expected 0 durable fails for denied event, got: %r" % (store.fail_calls,))

    if len(adapter.publish_calls) != 1:
        _add("expected exactly 1 delivery, got: %r" % (len(adapter.publish_calls),))
    elif adapter.publish_calls[0].event_id != "evt-ok":
        _add("expected only evt-ok to be delivered, got publish calls: %r" % ([e.event_id for e in adapter.publish_calls],))
    else:
        print("OK: rate-limiter denial skips delivery without ack/fail or outcome emission")
except Exception as e:
    _add("rate-limit skip scenario raised: %r" % (e,))


print("=== VALIDATE: processor with rate limiter and None emitter does not crash ===")
try:
    store = AckOnlyStore([_event(event_id="evt-none-emitter")])
    limiter = TokenBucketRateLimiter(capacity=5, refill_seconds=30, max_wait_seconds=0, now=datetime(2026, 9, 9, 12, 0, 0, tzinfo=timezone.utc))
    ack = DeliveryAcknowledgement(publish_ack_ref="ack-none")
    adapter = _FakeAdapter([ack])
    proc = OutboxProcessor(
        store=store,
        adapter=adapter,
        settings=ProcessingSettings(worker_id="w-ne", organization_id="o-1", batch_size=1),
        rate_limiter=limiter,
        emitter=None,
    )
    summary = proc.run_once()
    if summary.claimed != 1 or summary.acknowledged != 1 or summary.failed != 0:
        _add("expected 1/1/0 with None emitter, got: %r" % (summary,))
    if len(store.ack_calls) != 1 or store.ack_calls[0]["publish_ack_ref"] != "ack-none":
        _add("expected durable ack preserved with None emitter, got: %r" % (store.ack_calls,))
    else:
        print("OK: rate limiter + None emitter runs cleanly and durable ack survives")
except Exception as e:
    _add("rate limiter + None emitter scenario raised: %r" % (e,))


if errors:
    for e in errors:
        print("ERROR:", e)
    sys.exit(1)

print("\nAll phase8 outbox delivery rate-limit assertions passed.")
