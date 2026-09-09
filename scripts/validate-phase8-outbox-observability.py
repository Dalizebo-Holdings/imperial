#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OBSERVABILITY = ROOT / "kernel/outbox/observability.py"
WORKER = ROOT / "kernel/outbox/runtime.py"

for path in (OBSERVABILITY, WORKER):
    if not path.exists():
        raise SystemExit(f"ERROR: missing file {path}")
    py_compile.compile(str(path), doraise=True)

spec = importlib.util.spec_from_file_location("outbox_obs", OBSERVABILITY)
if spec is None or spec.loader is None:
    raise SystemExit("ERROR: unable to load outbox observability module")
obs = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = obs
spec.loader.exec_module(obs)

kernel_sink = obs.InMemoryStructuredLogSink()
emitter = obs.OutboxObservabilityEmitter(
    sink=kernel_sink,
    correlation_id="corr-obs-validate",
    organization_id="org-obs-validate",
    worker_id="worker-obs-validate",
    lease_seconds=60,
)
emitter.validate()

fact = obs.OutboxEventLogFact(
    event_id="evt-obs-validate",
    organization_id="org-obs-validate",
    workspace_id="ws-obs-validate",
    project_id="proj-obs-validate",
    environment_id="env-obs-validate",
    event_type="order.created",
    event_version="1",
    correlation_id="corr-obs-validate",
    resource_type="ORDER",
    resource_id="order-obs-validate",
    attempt_count=1,
    max_attempts=3,
    subscription_id="sub-obs-validate",
    delivery_id="delivery-obs-validate",
    error_code=None,
    next_attempt_at=None,
    lock_owner="worker-obs-validate",
    lock_expires_at="2026-09-09T12:00:00+00:00",
)

claimed = emitter.emit_claimed(fact=fact)
if claimed["event"] != obs.CLAIMED_EVENT:
    raise SystemExit("ERROR: claim log event name mismatch")
if claimed["fields"]["outcome"] != "claimed":
    raise SystemExit("ERROR: claim outcome mismatch")
if claimed["fields"]["lock_owner"] != "worker-obs-validate":
    raise SystemExit("ERROR: claim lock_owner not preserved")

refreshed = emitter.emit_lease_refreshed(fact=fact)
if refreshed["event"] != obs.LEASE_REFRESHED_EVENT:
    raise SystemExit("ERROR: lease refreshed event name mismatch")
if refreshed["fields"]["lease_seconds"] != 60:
    raise SystemExit("ERROR: lease seconds not recorded")

released = emitter.emit_lease_released(fact=fact)
if released["event"] != obs.LEASE_RELEASED_EVENT:
    raise SystemExit("ERROR: lease released event name mismatch")

rejected = emitter.emit_claim_rejected(reason="expired_lock", fact=None)
if rejected["event"] != obs.CLAIM_REJECTED_EVENT:
    raise SystemExit("ERROR: claim rejected event name mismatch")
if rejected["fields"]["reason"] != "expired_lock":
    raise SystemExit("ERROR: claim rejected reason not preserved")

published = emitter.emit_delivery_published(
    fact=fact,
    published_at="2026-09-09T12:00:01+00:00",
)
if published["event"] != obs.DELIVERED_EVENT:
    raise SystemExit("ERROR: delivery published event name mismatch")
if published["fields"]["delivery_id"] != "delivery-obs-validate":
    raise SystemExit("ERROR: delivery published delivery_id not preserved")

retry = emitter.emit_retry_scheduled(
    fact=fact,
    error_code="TEMPORARY_FAILURE",
    next_attempt_at="2026-09-09T12:01:00+00:00",
)
if retry["event"] != obs.RETRY_SCHEDULED_EVENT:
    raise SystemExit("ERROR: retry scheduled event name mismatch")
if retry["fields"]["next_attempt_at"] != "2026-09-09T12:01:00+00:00":
    raise SystemExit("ERROR: retry next_attempt_at not preserved")

dead = emitter.emit_dead_letter(fact=fact, error_code="FINAL_FAILURE")
if dead["event"] != obs.DEAD_LETTER_EVENT:
    raise SystemExit("ERROR: dead letter event name mismatch")
if dead["fields"]["outcome"] != "dead_letter":
    raise SystemExit("ERROR: dead letter outcome mismatch")

fact2 = obs.OutboxEventLogFact(
    event_id="evt-obs-redact",
    organization_id="org-obs-redact",
    workspace_id=None,
    project_id=None,
    environment_id=None,
    event_type="order.created",
    event_version="1",
    correlation_id="corr-obs-redact",
    resource_type="ORDER",
    resource_id="order-obs-redact",
    attempt_count=1,
    max_attempts=3,
    subscription_id=None,
    delivery_id=None,
    error_code=None,
    next_attempt_at=None,
    lock_owner=None,
    lock_expires_at="2026-09-09T12:00:00+00:00",
)
emitter2 = obs.OutboxObservabilityEmitter(
    sink=kernel_sink,
    correlation_id="corr-obs-redact",
    organization_id="org-obs-redact",
    worker_id="worker-obs-redact",
    lease_seconds=60,
)
emitter2.validate()
emitter2.emit_claimed(
    fact=fact2,
)

redacted = obs._safe_outbox_fields(
    {"order_id": "ok", "api_key": "secret-123", "nested": {"password": "hidden"}}
)
if redacted["api_key"] != "[REDACTED]":
    raise SystemExit("ERROR: outbox observability redaction is broken")
if redacted["nested"]["password"] != "[REDACTED]":
    raise SystemExit("ERROR: outbox observability recursive redaction is broken")

row = {
    "event_id": "evt-row",
    "organization_id": "org-row",
    "workspace_id": "ws-row",
    "project_id": "proj-row",
    "environment_id": "env-row",
    "event_type": "order.created",
    "event_version": "1",
    "correlation_id": "corr-row",
    "resource_type": "ORDER",
    "resource_id": "order-row",
    "attempt_count": 2,
    "max_attempts": 5,
    "lock_owner": "worker-row",
    "lock_expires_at": "2026-09-09T12:00:00+00:00",
}
built = obs.OutboxObservabilityEmitter.build_fact_from_row(row)
if built.event_id != "evt-row":
    raise SystemExit("ERROR: build_fact_from_row did not preserve event_id")
if built.workspace_id != "ws-row":
    raise SystemExit("ERROR: build_fact_from_row lost workspace context")
if built.attempt_count != 2:
    raise SystemExit("ERROR: build_fact_from_row attempt_count invalid")

try:
    obs.OutboxObservabilityEmitter(
        sink=kernel_sink,
        correlation_id="",
        organization_id="org-bad",
        worker_id="worker-bad",
        lease_seconds=60,
    ).validate()
except obs.OutboxObservabilityError:
    pass
else:
    raise SystemExit("ERROR: invalid emitter accepted")

print("OK: kernel outbox observability contract present")
print("OK: claim / lease refresh / lease release / claim rejected events emitted")
print("OK: delivery published / retry scheduled / dead letter events emitted")
print("OK: outbox observability preserves structured fact fields")
print("OK: outbox observability redacts sensitive fields via Kernel sink")
print("OK: build_fact_from_row preserves tenant and attempt context")
print("STATUS: PHASE 8 OUTBOX OBSERVABILITY READY")
