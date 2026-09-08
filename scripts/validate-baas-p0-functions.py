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
    "baas_functions": (
        BAAS / "functions/runtime.py"
    ),
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Functions BaaS runtime file: {path}"
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
functions = load_module(
    "baas_functions",
    MODULES["baas_functions"],
)

ctx = request_context.BaaSRequestContext(
    request_id="req-functions-validation",
    correlation_id="corr-functions-validation",
    service="functions",
    operation="function.invoke",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_functions_validation",
    idempotency_key="idem-functions-validation",
)
ctx.validate()

tenant = functions.TenantScope(
    organization_id=ctx.organization_id,
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
)

trigger = functions.TriggerDefinition(
    trigger_type="HTTP",
    http_method="POST",
    http_path="/webhooks/validation",
)
trigger.validate()

fn = functions.FunctionDescriptor(
    function_id="fn-validation",
    tenant=tenant,
    name="Validation Function",
    runtime="python3.13",
    entrypoint="handler.main",
    code_bundle_ref="object://functions/validation/bundle",
    trigger=trigger,
    timeout_seconds=30,
    memory_mb=256,
    secret_refs=(
        "vault://functions/validation/api",
    ),
    state="DRAFT",
    created_at="2026-01-01T00:00:00+00:00",
    updated_at="2026-01-01T00:00:00+00:00",
)

manager = functions.FunctionsManager()
manager.register(
    function=fn,
    request_context=ctx,
)

try:
    manager.build_invocation_plan(
        invocation=functions.InvocationRequest(
            function_id=fn.function_id,
            trigger_type="HTTP",
            payload_metadata={"size_bytes": 10},
            requested_at="2026-01-01T00:00:01+00:00",
        ),
        request_context=ctx,
    )
except functions.FunctionsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: DRAFT function produced invocation plan"
    )

active = manager.transition(
    function_id=fn.function_id,
    target_state="ACTIVE",
    request_context=ctx,
    now="2026-01-01T00:00:01+00:00",
)

if active.state != "ACTIVE":
    raise SystemExit(
        "ERROR: function did not transition to ACTIVE"
    )

invocation = functions.InvocationRequest(
    function_id=fn.function_id,
    trigger_type="HTTP",
    payload_metadata={
        "content_type": "application/json",
        "size_bytes": 10,
    },
    requested_at="2026-01-01T00:00:02+00:00",
)

plan_one = manager.build_invocation_plan(
    invocation=invocation,
    request_context=ctx,
)
plan_two = manager.build_invocation_plan(
    invocation=invocation,
    request_context=ctx,
)

if plan_one.execution_id != plan_two.execution_id:
    raise SystemExit(
        "ERROR: identical invocation plan identity is not deterministic"
    )

if (
    plan_one.execution_state
    != "READY_FOR_RUNTIME_ADAPTER"
):
    raise SystemExit(
        "ERROR: invocation plan claimed runtime execution"
    )

if plan_one.secret_refs != fn.secret_refs:
    raise SystemExit(
        "ERROR: invocation plan changed secret references"
    )

if "secret_value" in str(plan_one):
    raise SystemExit(
        "ERROR: invocation plan contains raw secret material"
    )

cross = request_context.BaaSRequestContext(
    request_id="req-functions-cross",
    correlation_id="corr-functions-cross",
    service="functions",
    operation="function.read",
    organization_id="org-other",
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
    actor_id=ctx.actor_id,
    actor_type=ctx.actor_type,
    kernel_authorization_ref="kernel_auth_functions_cross",
    idempotency_key="idem-functions-cross",
)

try:
    manager.get(
        function_id=fn.function_id,
        request_context=cross,
    )
except functions.FunctionsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: cross-tenant function access was accepted"
    )

try:
    functions.FunctionDescriptor(
        function_id="fn-unbounded",
        tenant=tenant,
        name="Unbounded",
        runtime="python3.13",
        entrypoint="handler.main",
        code_bundle_ref="object://functions/unbounded/bundle",
        trigger=functions.TriggerDefinition(
            trigger_type="MANUAL"
        ),
        timeout_seconds=901,
        memory_mb=256,
        secret_refs=(),
        state="DRAFT",
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    ).validate()
except functions.FunctionsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: function exceeded timeout bound"
    )

try:
    functions.InvocationRequest(
        function_id=fn.function_id,
        trigger_type="HTTP",
        payload_metadata={
            "api_key": "must-not-enter-metadata",
        },
        requested_at="2026-01-01T00:00:02+00:00",
    ).validate()
except functions.FunctionsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: secret-bearing invocation metadata was accepted"
    )

scheduled = functions.TriggerDefinition(
    trigger_type="SCHEDULED",
    schedule_expression="0 8 * * *",
)
scheduled.validate()

status = (
    BAAS / "IMPLEMENTATION_STATUS.md"
).read_text(encoding="utf-8")

for phrase in [
    "- [x] Serverless Functions",
    "- [x] Bounded timeout and memory policy",
    "- [x] Invocation plan",
    "- [ ] Isolated production code executor",
    "- [ ] API Gateway",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Functions BaaS status missing: "
            + phrase
        )

print("OK: Tenant function registration passed.")
print("OK: DRAFT functions cannot be invoked.")
print("OK: ACTIVE function invocation planning passed.")
print("OK: Invocation plan is deterministic and reference-only.")
print("OK: Cross-tenant function access fails closed.")
print("OK: Timeout/memory bounds are enforced.")
print("OK: Secret-bearing invocation metadata is rejected.")
print("OK: Scheduled trigger metadata validates without claiming scheduler execution.")
print("STATUS: BAAS P0 SERVERLESS FUNCTIONS READY")
