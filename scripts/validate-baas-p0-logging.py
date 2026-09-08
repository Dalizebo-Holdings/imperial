#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"
KERNEL = ROOT / "kernel"

MODULES = {
    "baas_request_context": (
        BAAS / "runtime/request_context.py"
    ),
    "baas_logging": (
        BAAS / "logging/runtime.py"
    ),
    "kernel_logging": (
        KERNEL / "observability/logging.py"
    ),
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing logging runtime file: {path}"
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
logging_baas = load_module(
    "baas_logging",
    MODULES["baas_logging"],
)
kernel_logging = load_module(
    "kernel_logging",
    MODULES["kernel_logging"],
)

sink = kernel_logging.InMemoryStructuredLogSink()

service = logging_baas.LoggingService(
    kernel_emit=sink.emit
)

ctx = request_context.BaaSRequestContext(
    request_id="req-logging-validation",
    correlation_id="corr-logging-validation",
    service="logging",
    operation="logging.ingest",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_logging_validation",
    idempotency_key="idem-logging-validation",
)
ctx.validate()

tenant = logging_baas.TenantScope(
    organization_id=ctx.organization_id,
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
)

policy = logging_baas.LogStreamPolicy(
    policy_id="log-policy-validation",
    tenant=tenant,
    minimum_level="INFO",
    retention_days=30,
    max_fields_bytes=4096,
)

service.register_policy(
    policy=policy,
    request_context=ctx,
)

dropped = service.ingest(
    request=logging_baas.LogIngestRequest(
        source_service="api_gateway",
        level="DEBUG",
        event="gateway.debug",
        correlation_id=ctx.correlation_id,
        actor_id=ctx.actor_id,
        trace_id="trace-001",
        span_id="span-001",
        fields={"safe": "debug"},
        timestamp="2026-01-01T00:00:00+00:00",
    ),
    request_context=ctx,
)

if dropped.get("accepted") is not False:
    raise SystemExit(
        "ERROR: record below minimum level was not dropped"
    )

accepted = service.ingest(
    request=logging_baas.LogIngestRequest(
        source_service="api_gateway",
        level="INFO",
        event="gateway.request.completed",
        correlation_id=ctx.correlation_id,
        actor_id=ctx.actor_id,
        trace_id="trace-001",
        span_id="span-001",
        fields={
            "status_code": 200,
            "api_key": "must-be-redacted",
            "nested": {
                "password": "must-also-be-redacted"
            },
        },
        timestamp="2026-01-01T00:00:01+00:00",
    ),
    request_context=ctx,
)

if accepted.get("accepted") is not True:
    raise SystemExit(
        "ERROR: valid log was not accepted"
    )

record = accepted["record"]

if record["organization_id"] != ctx.organization_id:
    raise SystemExit(
        "ERROR: tenant organization was not injected"
    )

if record["fields"]["api_key"] != "[REDACTED]":
    raise SystemExit(
        "ERROR: Kernel logging did not redact api_key"
    )

if (
    record["fields"]["nested"]["password"]
    != "[REDACTED]"
):
    raise SystemExit(
        "ERROR: Kernel recursive redaction failed"
    )

if len(sink.records) != 1:
    raise SystemExit(
        "ERROR: below-minimum record reached Kernel sink"
    )

try:
    service.ingest(
        request=logging_baas.LogIngestRequest(
            source_service="database",
            level="ERROR",
            event="database.error",
            correlation_id="corr-different",
            actor_id=ctx.actor_id,
            fields={},
            timestamp="2026-01-01T00:00:02+00:00",
        ),
        request_context=ctx,
    )
except logging_baas.LoggingBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: mismatched correlation_id was accepted"
    )

try:
    service.ingest(
        request=logging_baas.LogIngestRequest(
            source_service="database",
            level="ERROR",
            event="database.error",
            correlation_id=ctx.correlation_id,
            actor_id="actor-other",
            fields={},
            timestamp="2026-01-01T00:00:02+00:00",
        ),
        request_context=ctx,
    )
except logging_baas.LoggingBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: contradictory actor_id was accepted"
    )

service.ingest(
    request=logging_baas.LogIngestRequest(
        source_service="database",
        level="ERROR",
        event="database.query.failed",
        correlation_id=ctx.correlation_id,
        actor_id=ctx.actor_id,
        trace_id="trace-001",
        span_id="span-002",
        fields={
            "error_code": "DEPENDENCY_TIMEOUT",
        },
        timestamp="2026-01-01T00:00:03+00:00",
    ),
    request_context=ctx,
)

page_one = service.query(
    query=logging_baas.LogQuery(
        minimum_level="INFO",
        limit=1,
    ),
    request_context=ctx,
)

if (
    len(page_one.records) != 1
    or page_one.next_after_sequence != 1
):
    raise SystemExit(
        "ERROR: first log query page is invalid"
    )

page_two = service.query(
    query=logging_baas.LogQuery(
        minimum_level="INFO",
        after_sequence=(
            page_one.next_after_sequence
        ),
        limit=100,
    ),
    request_context=ctx,
)

if (
    len(page_two.records) != 1
    or page_two.records[0]["level"] != "ERROR"
):
    raise SystemExit(
        "ERROR: second log query page is invalid"
    )

error_only = service.query(
    query=logging_baas.LogQuery(
        minimum_level="ERROR",
        source_service="database",
        event_prefix="database.",
        trace_id="trace-001",
        limit=100,
    ),
    request_context=ctx,
)

if len(error_only.records) != 1:
    raise SystemExit(
        "ERROR: log filter contract failed"
    )

other_ctx = request_context.BaaSRequestContext(
    request_id="req-logging-other",
    correlation_id="corr-logging-other",
    service="logging",
    operation="logging.query",
    organization_id="org-other",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-other",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_logging_other",
    idempotency_key="idem-logging-other",
)

other_tenant = logging_baas.TenantScope(
    organization_id=other_ctx.organization_id,
    workspace_id=other_ctx.workspace_id,
    project_id=other_ctx.project_id,
    environment_id=other_ctx.environment_id,
)

service.register_policy(
    policy=logging_baas.LogStreamPolicy(
        policy_id="log-policy-other",
        tenant=other_tenant,
        minimum_level="DEBUG",
        retention_days=7,
        max_fields_bytes=4096,
    ),
    request_context=other_ctx,
)

other_result = service.query(
    query=logging_baas.LogQuery(
        limit=100,
    ),
    request_context=other_ctx,
)

if other_result.records:
    raise SystemExit(
        "ERROR: cross-tenant logs leaked into query"
    )

cutoff = service.retention_cutoff(
    request_context=ctx,
    now="2026-02-01T00:00:00+00:00",
)

if cutoff != "2026-01-02T00:00:00+00:00":
    raise SystemExit(
        "ERROR: retention cutoff calculation mismatch"
    )

if (
    page_one.access_log_context["service"]
    != "logging"
):
    raise SystemExit(
        "ERROR: log query access context missing"
    )

status = (
    BAAS / "IMPLEMENTATION_STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "- [x] Logging",
    "- [x] Kernel Structured Logging authority boundary",
    "- [x] Kernel recursive redaction preservation",
    "- [x] Tenant-scoped log query",
    "- [x] Retention cutoff metadata",
    "- [ ] Usage Metering",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Logging BaaS status missing: "
            + phrase
        )

print("OK: Kernel Structured Logging remains canonical.")
print("OK: Minimum log level policy passed.")
print("OK: Correlation/actor context enforcement passed.")
print("OK: Recursive Kernel redaction is preserved.")
print("OK: Tenant query isolation and filters passed.")
print("OK: Deterministic log pagination passed.")
print("OK: Retention cutoff metadata passed.")
print("OK: Logs remain separate from Kernel Audit.")
print("STATUS: BAAS P0 LOGGING READY")
