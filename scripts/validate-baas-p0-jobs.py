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
    "baas_jobs": (
        BAAS / "jobs/runtime.py"
    ),
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Background Jobs runtime file: {path}"
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
jobs = load_module(
    "baas_jobs",
    MODULES["baas_jobs"],
)

ctx = request_context.BaaSRequestContext(
    request_id="req-jobs-validation",
    correlation_id="corr-jobs-validation",
    service="background_jobs",
    operation="job.submit",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_jobs_validation",
    idempotency_key="idem-request-validation",
)
ctx.validate()

tenant = jobs.TenantScope(
    organization_id=ctx.organization_id,
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
)

definition = jobs.JobDefinition(
    definition_id="jobdef-order-reconcile",
    tenant=tenant,
    job_type="order.reconcile",
    handler_ref="function://jobs/order-reconcile",
    timeout_seconds=60,
    max_attempts=2,
    queue_name="commerce",
)

manager = jobs.BackgroundJobsManager()
manager.register_definition(
    definition=definition,
    request_context=ctx,
)

submission = jobs.JobSubmission(
    submission_id="submission-001",
    definition_id=definition.definition_id,
    idempotency_key="order-001-reconcile",
    mode="QUEUED",
    payload_metadata={
        "order_id": "order-001",
    },
    requested_at="2026-01-01T00:00:00+00:00",
)

first = manager.submit(
    submission=submission,
    request_context=ctx,
)
second = manager.submit(
    submission=submission,
    request_context=ctx,
)

if first.job_id != second.job_id:
    raise SystemExit(
        "ERROR: identical idempotent job submission changed job_id"
    )

try:
    manager.submit(
        submission=jobs.JobSubmission(
            submission_id="submission-conflict",
            definition_id=definition.definition_id,
            idempotency_key="order-001-reconcile",
            mode="QUEUED",
            payload_metadata={
                "order_id": "order-002",
            },
            requested_at="2026-01-01T00:00:00+00:00",
        ),
        request_context=ctx,
    )
except jobs.JobsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: idempotency key accepted different payload"
    )

plan = manager.build_dispatch_plan(
    job_id=first.job_id,
    pillars_approval_ref="pillars_validation_001",
    request_context=ctx,
    now="2026-01-01T00:00:00+00:00",
)

if plan.dispatch_state != "READY_FOR_LOOP_OS_ADAPTER":
    raise SystemExit(
        "ERROR: BaaS Jobs claimed direct worker execution"
    )

if not plan.kernel_authorization_ref.startswith(
    "kernel_auth_"
):
    raise SystemExit(
        "ERROR: Kernel authorization evidence was lost"
    )

if not plan.pillars_approval_ref.startswith(
    "pillars_"
):
    raise SystemExit(
        "ERROR: Pillars approval evidence was lost"
    )

if hasattr(plan, "kernel_authorized"):
    raise SystemExit(
        "ERROR: BaaS Jobs synthesized Loop OS authorization boolean"
    )

failed = manager.record_failure(
    job_id=first.job_id,
    error_code="HANDLER_TIMEOUT",
    request_context=ctx,
    now="2026-01-01T00:00:01+00:00",
)

if (
    failed.state != "RETRY_PENDING"
    or failed.attempt != 1
):
    raise SystemExit(
        "ERROR: first failed job did not enter RETRY_PENDING"
    )

try:
    manager.build_dispatch_plan(
        job_id=first.job_id,
        pillars_approval_ref="pillars_validation_001",
        request_context=ctx,
        now="2026-01-01T00:00:30+00:00",
    )
except jobs.JobsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: retry was dispatched before backoff expired"
    )

retry_plan = manager.build_dispatch_plan(
    job_id=first.job_id,
    pillars_approval_ref="pillars_validation_001",
    request_context=ctx,
    now="2026-01-01T00:00:31+00:00",
)

if retry_plan.attempt != 2:
    raise SystemExit(
        "ERROR: retry plan attempt mismatch"
    )

dead = manager.record_failure(
    job_id=first.job_id,
    error_code="HANDLER_TIMEOUT",
    request_context=ctx,
    now="2026-01-01T00:00:32+00:00",
)

if dead.state != "DEAD_LETTER":
    raise SystemExit(
        "ERROR: exhausted job did not enter DEAD_LETTER"
    )

observation = manager.observation(
    job_id=first.job_id,
    request_context=ctx,
)

if observation["state"] != "DEAD_LETTER":
    raise SystemExit(
        "ERROR: job failure is not visible through observation"
    )

delayed = manager.submit(
    submission=jobs.JobSubmission(
        submission_id="submission-delayed",
        definition_id=definition.definition_id,
        idempotency_key="delayed-001",
        mode="DELAYED",
        payload_metadata={
            "order_id": "order-delayed",
        },
        requested_at="2026-01-01T01:00:00+00:00",
        available_at="2026-01-01T02:00:00+00:00",
    ),
    request_context=ctx,
)

if delayed.state != "DELAYED":
    raise SystemExit(
        "ERROR: delayed job state mismatch"
    )

scheduled = manager.submit(
    submission=jobs.JobSubmission(
        submission_id="submission-scheduled",
        definition_id=definition.definition_id,
        idempotency_key="scheduled-001",
        mode="SCHEDULED",
        payload_metadata={
            "scope": "daily-reconcile",
        },
        requested_at="2026-01-01T01:00:00+00:00",
        available_at="2026-01-02T08:00:00+00:00",
        schedule_expression="0 8 * * *",
    ),
    request_context=ctx,
)

if (
    scheduled.state != "SCHEDULED"
    or scheduled.schedule_expression != "0 8 * * *"
):
    raise SystemExit(
        "ERROR: scheduled job metadata mismatch"
    )

cross = request_context.BaaSRequestContext(
    request_id="req-jobs-cross",
    correlation_id="corr-jobs-cross",
    service="background_jobs",
    operation="job.read",
    organization_id="org-other",
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
    actor_id=ctx.actor_id,
    actor_type=ctx.actor_type,
    kernel_authorization_ref="kernel_auth_jobs_cross",
    idempotency_key="idem-jobs-cross",
)

try:
    manager.get(
        job_id=delayed.job_id,
        request_context=cross,
    )
except jobs.JobsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: cross-tenant job access was accepted"
    )

try:
    jobs.JobSubmission(
        submission_id="submission-secret",
        definition_id=definition.definition_id,
        idempotency_key="secret-001",
        mode="QUEUED",
        payload_metadata={
            "api_key": "must-not-enter-job"
        },
        requested_at="2026-01-01T00:00:00+00:00",
    ).validate()
except jobs.JobsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: secret-bearing job payload was accepted"
    )

status = (
    BAAS / "IMPLEMENTATION_STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "- [x] Background Jobs",
    "- [x] Deterministic idempotent submission",
    "- [x] Bounded retry/backoff metadata",
    "- [x] Dead-letter terminal state",
    "- [x] Loop OS handoff plan",
    "- [x] Audit",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Background Jobs status missing: "
            + phrase
        )

print("OK: Queued/delayed/scheduled job contracts passed.")
print("OK: Idempotent duplicate submission returns one job identity.")
print("OK: Idempotency payload conflicts fail closed.")
print("OK: Loop OS handoff preserves authorization evidence without synthesizing booleans.")
print("OK: Retry backoff and max-attempt bounds passed.")
print("OK: Exhausted job enters DEAD_LETTER and remains observable.")
print("OK: Cross-tenant job access fails closed.")
print("OK: Secret-bearing job payloads are rejected.")
print("STATUS: BAAS P0 BACKGROUND JOBS READY")
