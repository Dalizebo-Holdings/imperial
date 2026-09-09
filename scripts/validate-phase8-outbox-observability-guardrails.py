#!/usr/bin/env python3
from __future__ import annotations

"""
Phase 8 outbox observability guardrails validator.

Validates that:
- OutboxObservabilityEmitter rejects empty source_service
- OutboxObservabilityEmitter rejects source_service values outside the known
  service set (kernel.outbox, kernel.outbox.worker, kernel.outbox.processor,
  baas.outbox)
- OutboxObservabilityEmitter rejects obviously forged source_service values
  even when they are plausible-looking (not in the known set)
- events are bound to the emitter's identity (correlation_id, organization_id,
  worker_id), not the fact's runtime identity
- payload or secret-bearing fields are not leaked through observability fields
- build_fact_from_row preserves tenant and attempt context
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from datetime import datetime, timezone

from kernel.outbox.observability import (
    OutboxEventLogFact,
    OutboxObservabilityEmitter,
    OutboxObservabilityError,
    InMemoryStructuredLogSink,
    OBSERVABLE_KNOWN_SERVICES,
)

errors: list[str] = []


def _add(msg: str) -> None:
    errors.append(msg)


def _now_iso() -> str:
    return "2026-09-09T12:00:00+00:00"


def _make_sink() -> InMemoryStructuredLogSink:
    return InMemoryStructuredLogSink()


def _make_emitter(*, source_service: str, worker_id: str = "w-obs", lease_seconds: int = 60) -> OutboxObservabilityEmitter:
    return OutboxObservabilityEmitter(
        sink=_make_sink(),
        correlation_id="corr-obs",
        organization_id="o-obs",
        worker_id=worker_id,
        lease_seconds=lease_seconds,
        source_service=source_service,
    )


def _fact(
    *,
    event_id: str = "evt-obs",
    organization_id: str = "o-obs",
    workspace_id: str | None = "ws-obs",
    project_id: str | None = "p-obs",
    environment_id: str | None = "e-obs",
    event_type: str = "webhook.dispatch.v1",
    event_version: str = "1",
    correlation_id: str = "corr-obs",
    resource_type: str = "webhook",
    resource_id: str = "wh-obs",
    attempt_count: int = 1,
    max_attempts: int = 5,
    subscription_id: str | None = None,
    delivery_id: str | None = None,
    error_code: str | None = None,
    next_attempt_at: str | None = None,
    lock_owner: str = "worker-obs",
    lock_expires_at: str = "2026-09-09T12:00:00+00:00",
) -> OutboxEventLogFact:
    return OutboxEventLogFact(
        event_id=event_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        project_id=project_id,
        environment_id=environment_id,
        event_type=event_type,
        event_version=event_version,
        correlation_id=correlation_id,
        resource_type=resource_type,
        resource_id=resource_id,
        attempt_count=attempt_count,
        max_attempts=max_attempts,
        subscription_id=subscription_id,
        delivery_id=delivery_id,
        error_code=error_code,
        next_attempt_at=next_attempt_at,
        lock_owner=lock_owner,
        lock_expires_at=lock_expires_at,
    )


print("=== VALIDATE: empty source_service is rejected ===")
try:
    emitter = _make_emitter(source_service="")
    try:
        emitter.validate()
        _add("expected OutboxObservabilityError for empty source_service")
    except OutboxObservabilityError:
        print("OK: empty source_service rejected")
except Exception as e:
    _add("empty source_service scenario raised: %r" % (e,))


print("=== VALIDATE: unknown source_service is rejected ===")
try:
    emitter = _make_emitter(source_service="kernel.outbox.monster")
    try:
        emitter.validate()
        _add("expected OutboxObservabilityError for unknown source_service")
    except OutboxObservabilityError:
        print("OK: unknown source_service rejected")
except Exception as e:
    _add("unknown source_service scenario raised: %r" % (e,))


print("=== VALIDATE: forged but plausible source_service values are rejected ===")
try:
    for candidate in (
        "kernel.outbox",
        "kernel.outbox.worker",
        "kernel.outbox.processor",
        "baas.outbox",
        "kernel.outbox.wrangler",
        "kernel.outbox_worker",
        "baas.outbox.delivery",
        "kernel.observability.outbox",
    ):
        emitter = _make_emitter(source_service=candidate)
        try:
            emitter.validate()
        except OutboxObservabilityError:
            if candidate in OBSERVABLE_KNOWN_SERVICES:
                _add("expected acceptance for known service %r, got error" % (candidate,))
            else:
                print("OK: forged source_service %r rejected" % (candidate,))
                continue
        else:
            if candidate not in OBSERVABLE_KNOWN_SERVICES:
                _add("expected rejection for non-known service %r, got acceptance" % (candidate,))
            else:
                print("OK: known source_service %r accepted" % (candidate,))
except Exception as e:
    _add("forged source_service scenario raised: %r" % (e,))


print("=== VALIDATE: emitter identity is bound to correlation/org/worker, not fact identity ===")
try:
    emitter = _make_emitter(source_service="kernel.outbox.worker", worker_id="w-bound")
    record = emitter.emit_claimed(fact=_fact(event_id="evt-different"))
    payload = record.get("fields") or {}
    top_level = record or {}
    if payload.get("event_id") != "evt-different":
        _add("claim event_id should match fact.event_id: %r" % (payload.get("event_id"),))
    if payload.get("correlation_id") != "corr-obs":
        _add("correlation_id should be emitter identity, not runtime correlation: %r" % (payload.get("correlation_id"),))
    if payload.get("organization_id") != "o-obs":
        _add("organization_id should be emitter identity: %r" % (payload.get("organization_id"),))
    if top_level.get("actor_id") != "w-bound":
        _add("actor_id should be emitter worker_id for claim: %r" % (top_level.get("actor_id"),))
    else:
        print("OK: emitter identity is bound to correlation/org/worker fields")
except Exception as e:
    _add("identity binding scenario raised: %r" % (e,))


print("=== VALIDATE: delivery_published uses emitter identity, not runtime correlation ===")
try:
    emitter = _make_emitter(source_service="kernel.outbox.worker", worker_id="w-delivery")
    record = emitter.emit_delivery_published(
        fact=_fact(event_id="evt-delivery", delivery_id="pub-ack-123"),
        published_at="2026-09-09T12:00:00+00:00",
    )
    payload = record.get("fields") or {}
    top_level = record or {}
    if payload.get("correlation_id") != "corr-obs":
        _add("delivery_published correlation_id should be emitter identity: %r" % (payload.get("correlation_id"),))
    if top_level.get("actor_id") != "w-delivery":
        _add("delivery_published actor_id should be emitter worker_id: %r" % (top_level.get("actor_id"),))
    if payload.get("published_at") != "2026-09-09T12:00:00+00:00":
        _add("delivery_published published_at should be passed through: %r" % (payload.get("published_at"),))
    else:
        print("OK: delivery_published binding is correct")
except Exception as e:
    _add("delivery_published binding scenario raised: %r" % (e,))


print("=== VALIDATE: observability fields do not leak payload or secret-bearing values ===")
try:
    secret_candidates = (
        "secret",
        "token",
        "api_key",
        "password",
        "client_secret",
        "private_key",
    )
    for record in [
        _make_emitter(source_service="kernel.outbox.processor").emit_claimed(fact=_fact()),
        _make_emitter(source_service="kernel.outbox.processor").emit_delivery_published(
            fact=_fact(delivery_id="pub-ack-456"),
            published_at=_now_iso(),
        ),
        _make_emitter(source_service="kernel.outbox.processor").emit_retry_scheduled(
            fact=_fact(),
            error_code="webhook.timeout",
            next_attempt_at=_now_iso(),
        ),
        _make_emitter(source_service="kernel.outbox.processor").emit_dead_letter(
            fact=_fact(),
            error_code="webhook.dead",
        ),
    ]:
        fields = record.get("fields", {})
        lowered = {k: str(v).lower() for k, v in fields.items()}
        for candidate in secret_candidates:
            for value in lowered.values():
                if candidate in value:
                    _add("observability field leaked sensitive term %r in %r" % (candidate, value))
    print("OK: observability fields do not leak payload or secret-bearing values")
except Exception as e:
    _add("leak scenario raised: %r" % (e,))


print("=== VALIDATE: build_fact_from_row preserves tenant and attempt context ===")
try:
    row = {
        "event_id": "evt-row",
        "organization_id": "o-row",
        "workspace_id": "ws-row",
        "project_id": "p-row",
        "environment_id": "e-row",
        "event_type": "webhook.dispatch.v1",
        "event_version": "1",
        "correlation_id": "corr-row",
        "resource_type": "webhook",
        "resource_id": "wh-row",
        "attempt_count": 2,
        "max_attempts": 5,
        "lock_owner": "worker-row",
        "lock_expires_at": _now_iso(),
    }
    fact = OutboxObservabilityEmitter.build_fact_from_row(row)
    if not isinstance(fact, OutboxEventLogFact):
        _add("build_fact_from_row must return OutboxEventLogFact, got %r" % (type(fact),))
    else:
        if fact.event_id != "evt-row":
            _add("event_id mismatch: %r" % (fact.event_id,))
        if fact.organization_id != "o-row":
            _add("organization_id mismatch: %r" % (fact.organization_id,))
        if fact.attempt_count != 2:
            _add("attempt_count mismatch: %r" % (fact.attempt_count,))
        if fact.max_attempts != 5:
            _add("max_attempts mismatch: %r" % (fact.max_attempts,))
        if fact.lock_owner != "worker-row":
            _add("lock_owner mismatch: %r" % (fact.lock_owner,))
        if fact.lock_expires_at != _now_iso():
            _add("lock_expires_at mismatch: %r" % (fact.lock_expires_at,))
        else:
            print("OK: build_fact_from_row preserves tenant and attempt context")
except Exception as e:
    _add("build_fact_from_row scenario raised: %r" % (e,))


if errors:
    for e in errors:
        print("ERROR:", e)
    sys.exit(1)

print("\nAll phase8 outbox observability guardrails assertions passed.")
