#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"

MODULES = {
    "baas_request_context": (
        BAAS / "runtime/request_context.py"
    ),
    "baas_events": (
        BAAS / "events/runtime.py"
    ),
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Events BaaS runtime file: {path}"
        )
    py_compile.compile(
        str(path),
        doraise=True,
    )

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(
        name,
        path,
    )

    if spec is None or spec.loader is None:
        raise SystemExit(
            f"ERROR: unable to load module: {path}"
        )

    module = importlib.util.module_from_spec(
        spec
    )
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

request_context = load_module(
    "baas_request_context",
    MODULES["baas_request_context"],
)
events = load_module(
    "baas_events",
    MODULES["baas_events"],
)

ctx = request_context.BaaSRequestContext(
    request_id="req-events-validation",
    correlation_id="corr-events-validation",
    service="events",
    operation="event.publish",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_events_validation",
    idempotency_key="idem-events-validation",
)
ctx.validate()

tenant = events.TenantScope(
    organization_id=ctx.organization_id,
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
)

manager = events.EventsManager()

subscription = events.Subscription(
    subscription_id="sub-order",
    tenant=tenant,
    event_pattern="order.*",
    target_type="FUNCTION",
    target_ref="function://order-projection",
    max_attempts=2,
)
manager.register_subscription(
    subscription=subscription,
    request_context=ctx,
)

event = events.EventEnvelope(
    event_id="evt-validation",
    event_type="order.created",
    event_version="1",
    tenant=tenant,
    resource_type="order",
    resource_id="ord-validation",
    occurred_at="2026-01-01T00:00:00+00:00",
    correlation_id=ctx.correlation_id,
    actor_type=ctx.actor_type,
    actor_id=ctx.actor_id,
    payload={
        "status": "CREATED",
        "total_minor": 1000,
        "currency": "ZAR",
    },
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
    raise SystemExit(
        "ERROR: uncommitted event was published"
    )

plans = manager.publish_committed(
    outbox_event=events.OutboxEvent(
        event=event,
        outbox_status="COMMITTED",
    ),
    request_context=ctx,
)

if len(plans) != 1:
    raise SystemExit(
        "ERROR: committed event did not create exactly one delivery"
    )

plan = plans[0]

if (
    plan.delivery_state
    != "READY_FOR_DELIVERY_ADAPTER"
):
    raise SystemExit(
        "ERROR: Events BaaS claimed network delivery"
    )

same_plans = manager.publish_committed(
    outbox_event=events.OutboxEvent(
        event=event,
        outbox_status="COMMITTED",
    ),
    request_context=ctx,
)

if (
    not same_plans
    or same_plans[0].delivery_id
    != plan.delivery_id
):
    raise SystemExit(
        "ERROR: event/subscription delivery identity is not deterministic"
    )

failed = manager.record_failure(
    delivery_id=plan.delivery_id,
    error_code="DELIVERY_TIMEOUT",
)

if (
    failed.state
    != "RETRY_PENDING"
    or failed.attempt != 2
):
    raise SystemExit(
        "ERROR: first delivery failure did not schedule bounded retry"
    )

retry = manager.retry_plan(
    delivery_id=plan.delivery_id,
)

if retry.attempt != 2:
    raise SystemExit(
        "ERROR: retry plan attempt mismatch"
    )

dead = manager.record_failure(
    delivery_id=plan.delivery_id,
    error_code="DELIVERY_TIMEOUT",
)

if dead.state != "DEAD_LETTER":
    raise SystemExit(
        "ERROR: exhausted delivery did not enter DEAD_LETTER"
    )

cross = request_context.BaaSRequestContext(
    request_id="req-events-cross",
    correlation_id="corr-events-cross",
    service="events",
    operation="subscription.create",
    organization_id="org-other",
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
    actor_id=ctx.actor_id,
    actor_type=ctx.actor_type,
    kernel_authorization_ref="kernel_auth_events_cross",
    idempotency_key="idem-events-cross",
)

try:
    manager.register_subscription(
        subscription=events.Subscription(
            subscription_id="sub-cross",
            tenant=tenant,
            event_pattern="*",
            target_type="INTERNAL",
            target_ref="internal://projection",
            max_attempts=1,
        ),
        request_context=cross,
    )
except events.EventsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: cross-tenant subscription registration was accepted"
    )

try:
    events.EventEnvelope(
        event_id="evt-secret",
        event_type="order.created",
        event_version="1",
        tenant=tenant,
        resource_type="order",
        resource_id="ord-secret",
        occurred_at="2026-01-01T00:00:00+00:00",
        correlation_id=ctx.correlation_id,
        actor_type=ctx.actor_type,
        actor_id=ctx.actor_id,
        payload={
            "api_key": "must-not-enter-event"
        },
    ).validate()
except events.EventsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: secret-bearing event payload was accepted"
    )

conflicting_event = events.EventEnvelope(
    event_id=event.event_id,
    event_type=event.event_type,
    event_version=event.event_version,
    tenant=tenant,
    resource_type=event.resource_type,
    resource_id=event.resource_id,
    occurred_at=event.occurred_at,
    correlation_id=event.correlation_id,
    actor_type=event.actor_type,
    actor_id=event.actor_id,
    payload={
        "status": "ALTERED"
    },
)

try:
    manager.publish_committed(
        outbox_event=events.OutboxEvent(
            event=conflicting_event,
            outbox_status="COMMITTED",
        ),
        request_context=ctx,
    )
except events.EventsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: conflicting reuse of event_id was accepted"
    )

status = (
    BAAS / "IMPLEMENTATION_STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "- [x] Events",
    "- [x] COMMITTED outbox publication gate",
    "- [x] Deterministic delivery identity",
    "- [x] Bounded retry metadata",
    "- [x] Dead-letter terminal state",
    "- [ ] Webhooks",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Events BaaS status missing: "
            + phrase
        )

print("OK: Kernel event envelope preservation passed.")
print("OK: Uncommitted outbox publication fails closed.")
print("OK: Tenant subscription matching passed.")
print("OK: Delivery identity is deterministic.")
print("OK: Retry attempts are bounded.")
print("OK: Exhausted delivery enters DEAD_LETTER.")
print("OK: Cross-tenant subscription access fails closed.")
print("OK: Secret-bearing payloads and event-id conflicts are rejected.")
print("STATUS: BAAS P0 EVENTS READY")
