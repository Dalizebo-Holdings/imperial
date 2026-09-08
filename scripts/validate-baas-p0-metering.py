#!/usr/bin/env python3
from pathlib import Path
from dataclasses import replace
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"

MODULES = {
    "baas_request_context": (
        BAAS / "runtime/request_context.py"
    ),
    "baas_metering": (
        BAAS / "metering/runtime.py"
    ),
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Usage Metering runtime file: {path}"
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
metering = load_module(
    "baas_metering",
    MODULES["baas_metering"],
)

ctx = request_context.BaaSRequestContext(
    request_id="req-metering-validation",
    correlation_id="corr-metering-validation",
    service="usage_metering",
    operation="usage.ingest",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="SERVICE_ACCOUNT",
    kernel_authorization_ref="kernel_auth_metering_validation",
    idempotency_key="idem-request-validation",
)
ctx.validate()

service = metering.UsageMeteringService()

event_one = metering.UsageEvent(
    submission_id="submission-001",
    producer="api_gateway",
    idempotency_key="request-001",
    metric="api_requests",
    unit="request",
    quantity="1.000",
    occurred_at="2026-01-01T00:00:00+00:00",
    dimensions={
        "route": "/api/v1/orders",
        "method": "POST",
    },
    source_ref="gateway://request/001",
)

first = service.ingest(
    event=event_one,
    request_context=ctx,
    ingested_at="2026-01-01T00:00:01+00:00",
)

if not first["created"]:
    raise SystemExit(
        "ERROR: first usage event was not created"
    )

if first["record"].quantity != "1":
    raise SystemExit(
        "ERROR: usage quantity was not canonicalized"
    )

second = service.ingest(
    event=event_one,
    request_context=ctx,
    ingested_at="2026-01-01T00:00:02+00:00",
)

if second["created"]:
    raise SystemExit(
        "ERROR: identical idempotent usage event created duplicate"
    )

if (
    second["record"].usage_id
    != first["record"].usage_id
):
    raise SystemExit(
        "ERROR: idempotent usage event changed usage_id"
    )

try:
    service.ingest(
        event=metering.UsageEvent(
            submission_id="submission-conflict",
            producer="api_gateway",
            idempotency_key="request-001",
            metric="api_requests",
            unit="request",
            quantity="2",
            occurred_at="2026-01-01T00:00:00+00:00",
            dimensions={
                "route": "/api/v1/orders",
                "method": "POST",
            },
            source_ref="gateway://request/001",
        ),
        request_context=ctx,
        ingested_at="2026-01-01T00:00:03+00:00",
    )
except metering.MeteringBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: idempotency key accepted conflicting usage event"
    )

service.ingest(
    event=metering.UsageEvent(
        submission_id="submission-002",
        producer="api_gateway",
        idempotency_key="request-002",
        metric="api_requests",
        unit="request",
        quantity="2",
        occurred_at="2026-01-01T00:10:00+00:00",
        dimensions={
            "route": "/api/v1/orders",
            "method": "GET",
        },
        source_ref="gateway://request/002",
    ),
    request_context=ctx,
    ingested_at="2026-01-01T00:10:01+00:00",
)

service.ingest(
    event=metering.UsageEvent(
        submission_id="submission-003",
        producer="database",
        idempotency_key="db-001",
        metric="database_storage",
        unit="byte_hour",
        quantity="1024.50",
        occurred_at="2026-01-01T00:20:00+00:00",
        dimensions={
            "database_id": "db-validation",
        },
        source_ref="database://usage/001",
    ),
    request_context=ctx,
    ingested_at="2026-01-01T00:20:01+00:00",
)

aggregate = service.aggregate(
    metric="api_requests",
    unit="request",
    period_start="2026-01-01T00:00:00+00:00",
    period_end="2026-01-02T00:00:00+00:00",
    request_context=ctx,
    generated_at="2026-01-02T00:00:01+00:00",
)

if aggregate.total_quantity != "3":
    raise SystemExit(
        "ERROR: metering aggregate total mismatch"
    )

if aggregate.event_count != 2:
    raise SystemExit(
        "ERROR: metering aggregate event count mismatch"
    )

if len(aggregate.source_usage_ids) != 2:
    raise SystemExit(
        "ERROR: aggregate source IDs mismatch"
    )

reconciliation = service.reconcile(
    aggregate=aggregate,
    request_context=ctx,
)

if not reconciliation["valid"]:
    raise SystemExit(
        "ERROR: valid aggregate failed reconciliation"
    )

tampered = replace(
    aggregate,
    total_quantity="999",
)

if service.reconcile(
    aggregate=tampered,
    request_context=ctx,
)["valid"]:
    raise SystemExit(
        "ERROR: tampered aggregate passed reconciliation"
    )

if first["audit_event"]["action"] != "usage_metering.ingest":
    raise SystemExit(
        "ERROR: ingestion audit evidence missing"
    )

if aggregate.audit_event["action"] != "usage_metering.aggregate":
    raise SystemExit(
        "ERROR: aggregation audit evidence missing"
    )

try:
    metering.UsageEvent(
        submission_id="submission-secret",
        producer="api_gateway",
        idempotency_key="request-secret",
        metric="api_requests",
        unit="request",
        quantity="1",
        occurred_at="2026-01-01T00:00:00+00:00",
        dimensions={
            "api_key": "must-not-enter-usage"
        },
        source_ref="gateway://request/secret",
    ).validate()
except metering.MeteringBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: secret-bearing usage dimensions were accepted"
    )

try:
    metering.canonical_quantity(
        "-1"
    )
except metering.MeteringBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: negative usage quantity was accepted"
    )

cross_ctx = request_context.BaaSRequestContext(
    request_id="req-metering-cross",
    correlation_id="corr-metering-cross",
    service="usage_metering",
    operation="usage.read",
    organization_id="org-other",
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
    actor_id="actor-other",
    actor_type="SERVICE_ACCOUNT",
    kernel_authorization_ref="kernel_auth_metering_cross",
    idempotency_key="idem-metering-cross",
)

try:
    service.get(
        usage_id=first["record"].usage_id,
        request_context=cross_ctx,
    )
except metering.MeteringBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: cross-tenant raw usage access was accepted"
    )

if len(metering.METRICS) != 10:
    raise SystemExit(
        "ERROR: canonical initial metered-resource count changed"
    )

status = (
    BAAS / "IMPLEMENTATION_STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "- [x] Usage Metering",
    "- [x] Timestamped immutable raw usage records",
    "- [x] Idempotent ingestion",
    "- [x] Unit-safe aggregation",
    "- [x] Reconciliation verification",
    "- [ ] Subscription Billing",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Usage Metering status missing: "
            + phrase
        )

print("OK: All 10 canonical initial metered resources are registered.")
print("OK: Tenant-attributed immutable raw usage ingestion passed.")
print("OK: Decimal quantities normalize without floating-point storage.")
print("OK: Idempotent duplicate ingestion returns one usage identity.")
print("OK: Idempotency conflicts fail closed.")
print("OK: Unit-safe deterministic aggregation passed.")
print("OK: Aggregate source-hash reconciliation passed.")
print("OK: Tampered aggregate fails reconciliation.")
print("OK: Cross-tenant raw usage access fails closed.")
print("STATUS: BAAS P0 USAGE METERING READY")
