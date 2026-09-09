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
    "baas_webhooks": (
        BAAS / "webhooks/runtime.py"
    ),
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Webhooks BaaS runtime file: {path}"
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
webhooks = load_module(
    "baas_webhooks",
    MODULES["baas_webhooks"],
)

ctx = request_context.BaaSRequestContext(
    request_id="req-webhook-validation",
    correlation_id="corr-webhook-validation",
    service="webhooks",
    operation="webhook.deliver",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_webhook_validation",
    idempotency_key="idem-webhook-validation",
)
ctx.validate()

tenant = webhooks.TenantScope(
    organization_id=ctx.organization_id,
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
)

endpoint = webhooks.WebhookEndpoint(
    endpoint_id="endpoint-validation",
    tenant=tenant,
    url="https://hooks.example.com/dalizebo",
    event_patterns=("order.*",),
    signing_secret_ref="vault://webhooks/validation/v1",
    signing_secret_version=1,
    timeout_seconds=10,
    max_attempts=2,
)

manager = webhooks.WebhooksManager()
manager.register_endpoint(
    endpoint=endpoint,
    request_context=ctx,
)

for bad_url in [
    "http://hooks.example.com/test",
    "https://127.0.0.1/test",
    "https://10.0.0.1/test",
    "https://user:pass@example.com/test",
]:
    try:
        webhooks.validate_webhook_url(
            bad_url
        )
    except webhooks.WebhooksBaaSError:
        pass
    else:
        raise SystemExit(
            "ERROR: unsafe webhook URL was accepted: "
            + bad_url
        )

event = webhooks.WebhookEvent(
    event_id="evt-webhook-validation",
    event_type="order.created",
    tenant=tenant,
    correlation_id=ctx.correlation_id,
    payload={
        "order_id": "ord-validation",
        "status": "CREATED",
    },
    occurred_at="2026-01-01T00:00:00+00:00",
)

plans = manager.plan_event(
    event=event,
    request_context=ctx,
)

if len(plans) != 1:
    raise SystemExit(
        "ERROR: webhook event did not create exactly one delivery"
    )

plan = plans[0]

if (
    plan.delivery_state
    != "READY_FOR_HTTPS_ADAPTER"
):
    raise SystemExit(
        "ERROR: webhook control plane claimed network delivery"
    )

repeat = manager.plan_event(
    event=event,
    request_context=ctx,
)

if (
    not repeat
    or repeat[0].delivery_id
    != plan.delivery_id
):
    raise SystemExit(
        "ERROR: initial webhook delivery identity is not deterministic"
    )

raw_body = b'{"order_id":"ord-validation"}'
raw_secret = b"x" * 32
timestamp = "2026-01-01T00:00:01+00:00"

signature = webhooks.sign_payload(
    raw_body=raw_body,
    raw_secret=raw_secret,
    timestamp=timestamp,
)

if not signature.startswith(
    "sha256="
):
    raise SystemExit(
        "ERROR: webhook signature format mismatch"
    )

if not webhooks.verify_signature(
    raw_body=raw_body,
    raw_secret=raw_secret,
    timestamp=timestamp,
    supplied_signature=signature,
):
    raise SystemExit(
        "ERROR: valid webhook signature failed verification"
    )

failed = manager.record_result(
    delivery_id=plan.delivery_id,
    success=False,
    http_status=503,
    error_code="HTTP_503",
)

if (
    failed.state
    != "RETRY_PENDING"
    or failed.attempt != 2
):
    raise SystemExit(
        "ERROR: first webhook failure did not schedule retry"
    )

retry_plan = manager.retry_plan(
    delivery_id=plan.delivery_id,
    request_context=ctx,
)

if retry_plan.attempt != 2:
    raise SystemExit(
        "ERROR: webhook retry attempt mismatch"
    )

dead = manager.record_result(
    delivery_id=plan.delivery_id,
    success=False,
    http_status=503,
    error_code="HTTP_503",
)

if dead.state != "DEAD_LETTER":
    raise SystemExit(
        "ERROR: exhausted webhook did not enter DEAD_LETTER"
    )

replay = manager.replay(
    delivery_id=plan.delivery_id,
    reason="operator replay after endpoint recovery",
    request_context=ctx,
)

if replay.delivery_id == plan.delivery_id:
    raise SystemExit(
        "ERROR: replay reused original delivery ID"
    )

rotated = manager.rotate_signing_secret(
    endpoint_id=endpoint.endpoint_id,
    new_secret_ref="vault://webhooks/validation/v2",
    request_context=ctx,
)

if (
    rotated.signing_secret_version != 2
):
    raise SystemExit(
        "ERROR: secret rotation did not increment version"
    )

if (
    rotated.signing_secret_ref
    == endpoint.signing_secret_ref
):
    raise SystemExit(
        "ERROR: secret rotation did not replace reference"
    )

cross = request_context.BaaSRequestContext(
    request_id="req-webhook-cross",
    correlation_id="corr-webhook-cross",
    service="webhooks",
    operation="webhook.rotate",
    organization_id="org-other",
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
    actor_id=ctx.actor_id,
    actor_type=ctx.actor_type,
    kernel_authorization_ref="kernel_auth_webhook_cross",
    idempotency_key="idem-webhook-cross",
)

try:
    manager.rotate_signing_secret(
        endpoint_id=endpoint.endpoint_id,
        new_secret_ref="vault://webhooks/validation/v3",
        request_context=cross,
    )
except webhooks.WebhooksBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: cross-tenant webhook endpoint access was accepted"
    )

try:
    webhooks.WebhookEvent(
        event_id="evt-secret",
        event_type="order.created",
        tenant=tenant,
        correlation_id=ctx.correlation_id,
        payload={
            "api_key": "must-not-send"
        },
        occurred_at="2026-01-01T00:00:00+00:00",
    ).validate()
except webhooks.WebhooksBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: secret-bearing webhook payload was accepted"
    )

status = (
    BAAS / "IMPLEMENTATION_STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "- [x] Webhooks",
    "- [x] HMAC-SHA256 signing contract",
    "- [x] Bounded timeout/retry policy",
    "- [x] Replay with linked delivery identity",
    "- [x] Signing-secret rotation metadata",
    "- [x] Background Jobs",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Webhooks BaaS status missing: "
            + phrase
        )

print("OK: HTTPS-only webhook endpoint policy passed.")
print("OK: Private/loopback literal targets are rejected.")
print("OK: HMAC-SHA256 signing and verification passed.")
print("OK: Deterministic initial delivery identity passed.")
print("OK: Retry/dead-letter lifecycle passed.")
print("OK: Replay creates linked new delivery identity.")
print("OK: Secret-reference rotation increments version.")
print("OK: Cross-tenant endpoint access fails closed.")
print("STATUS: BAAS P0 WEBHOOKS READY")
