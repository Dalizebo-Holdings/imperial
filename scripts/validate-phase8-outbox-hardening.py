#!/usr/bin/env python3
from pathlib import Path
from types import SimpleNamespace
import importlib.util
import sys

ROOT = Path(__file__).resolve().parent.parent
migration = ROOT / "kernel/migrations/sql/0004_phase8_outbox_delivery_hardening.sql"
runtime_path = ROOT / "baas/events/runtime.py"

sql = migration.read_text()

for marker in [
    "attempt_count",
    "max_attempts",
    "next_attempt_at",
    "lock_owner",
    "lock_expires_at",
    "RETRY_PENDING",
    "DEAD_LETTER",
    "idx_outbox_claimable",
]:
    if marker not in sql:
        raise SystemExit(f"ERROR: migration missing {marker}")

spec = importlib.util.spec_from_file_location("phase8_events", runtime_path)
events = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = events
spec.loader.exec_module(events)

tenant = events.TenantScope(
    organization_id="org_phase8",
    workspace_id="ws_phase8",
    project_id="proj_phase8",
    environment_id="env_phase8",
)

ctx = SimpleNamespace(
    organization_id="org_phase8",
    workspace_id="ws_phase8",
    project_id="proj_phase8",
    environment_id="env_phase8",
    kernel_authorization_ref="kernel_auth_phase8",
    correlation_id="corr_phase8",
    actor_id="worker_phase8",
)

manager = events.EventsManager()

manager.register_subscription(
    subscription=events.Subscription(
        subscription_id="sub_phase8",
        tenant=tenant,
        event_pattern="order.*",
        target_type="INTERNAL",
        target_ref="internal://phase8-test",
        max_attempts=2,
    ),
    request_context=ctx,
)

event = events.EventEnvelope(
    event_id="evt_phase8",
    event_type="order.created",
    event_version="1",
    tenant=tenant,
    resource_type="ORDER",
    resource_id="order_phase8",
    occurred_at="2026-09-09T14:00:00+00:00",
    correlation_id="corr_phase8",
    actor_type="SYSTEM",
    actor_id="worker_phase8",
    payload={"order_id": "order_phase8"},
)

try:
    manager.publish_committed(
        outbox_event=events.OutboxEvent(
            event=event,
            outbox_status="STAGED",
        ),
        request_context=ctx,
    )
except events.EventsBaaSError:
    pass
else:
    raise SystemExit("ERROR: uncommitted event publication accepted")

plans = manager.publish_committed(
    outbox_event=events.OutboxEvent(
        event=event,
        outbox_status="COMMITTED",
    ),
    request_context=ctx,
)

if len(plans) != 1 or plans[0].attempt != 1:
    raise SystemExit("ERROR: initial delivery plan invalid")

first = manager.record_failure(
    delivery_id=plans[0].delivery_id,
    error_code="TEMPORARY_FAILURE",
)

if first.state != "RETRY_PENDING" or first.attempt != 2:
    raise SystemExit("ERROR: retry transition invalid")

retry = manager.retry_plan(delivery_id=plans[0].delivery_id)

if retry.attempt != 2:
    raise SystemExit("ERROR: retry plan attempt invalid")

terminal = manager.record_failure(
    delivery_id=plans[0].delivery_id,
    error_code="FINAL_FAILURE",
)

if terminal.state != "DEAD_LETTER":
    raise SystemExit("ERROR: dead-letter transition invalid")

replay = manager.publish_committed(
    outbox_event=events.OutboxEvent(
        event=event,
        outbox_status="COMMITTED",
    ),
    request_context=ctx,
)

if replay:
    raise SystemExit("ERROR: DEAD_LETTER delivery was replanned")

print("OK: durable outbox migration controls present")
print("OK: committed-only publication")
print("OK: bounded retry progression")
print("OK: dead-letter terminal replay protection")
print("STATUS: PHASE 8 OUTBOX PERSISTENCE HARDENING READY")
