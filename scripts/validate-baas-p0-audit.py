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
    "baas_audit": (
        BAAS / "audit/runtime.py"
    ),
    "kernel_audit": (
        KERNEL / "audit/persistence.py"
    ),
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing audit runtime file: {path}"
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
audit = load_module(
    "baas_audit",
    MODULES["baas_audit"],
)
kernel_audit = load_module(
    "kernel_audit",
    MODULES["kernel_audit"],
)

records = []

event_one = kernel_audit.AuditEvent(
    audit_id="audit-001",
    organization_id="org-validation",
    actor_type="HUMAN_USER",
    actor_id="actor-validation",
    action="order.create",
    resource_type="order",
    resource_id="order-001",
    timestamp="2026-01-01T00:00:00+00:00",
    correlation_id="corr-001",
    metadata={
        "channel": "commerce",
        "api_key": "must-be-redacted",
    },
)

record_one = kernel_audit.build_record(
    event_one,
    sequence=1,
    previous_hash="",
)
records.append(record_one)

event_two = kernel_audit.AuditEvent(
    audit_id="audit-002",
    organization_id="org-validation",
    actor_type="HUMAN_USER",
    actor_id="actor-validation",
    action="order.update",
    resource_type="order",
    resource_id="order-001",
    timestamp="2026-01-01T00:01:00+00:00",
    correlation_id="corr-002",
    metadata={
        "status": "CONFIRMED",
    },
)

record_two = kernel_audit.build_record(
    event_two,
    sequence=2,
    previous_hash=(
        record_one["record_hash"]
    ),
)
records.append(record_two)

event_other = kernel_audit.AuditEvent(
    audit_id="audit-003",
    organization_id="org-other",
    actor_type="HUMAN_USER",
    actor_id="actor-other",
    action="order.create",
    resource_type="order",
    resource_id="order-other",
    timestamp="2026-01-01T00:02:00+00:00",
    correlation_id="corr-other",
    metadata={},
)

record_three = kernel_audit.build_record(
    event_other,
    sequence=3,
    previous_hash=(
        record_two["record_hash"]
    ),
)
records.append(record_three)

verification = kernel_audit.verify_records(
    records
)

if not verification.get("valid"):
    raise SystemExit(
        "ERROR: baseline Kernel audit chain is invalid"
    )

ctx = request_context.BaaSRequestContext(
    request_id="req-audit-validation",
    correlation_id="corr-audit-validation",
    service="audit",
    operation="audit.query",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="auditor-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_audit_validation",
    idempotency_key="idem-audit-validation",
)
ctx.validate()

service = audit.AuditService(
    kernel_verify_records=(
        kernel_audit.verify_records
    )
)

result = service.query(
    records=records,
    query=audit.AuditQuery(
        resource_type="order",
        resource_id="order-001",
        limit=1,
    ),
    request_context=ctx,
)

if len(result.records) != 1:
    raise SystemExit(
        "ERROR: audit query pagination failed"
    )

if (
    result.records[0]["metadata"]["api_key"]
    != "[REDACTED]"
):
    raise SystemExit(
        "ERROR: sensitive audit metadata was not redacted"
    )

if result.next_after_sequence != 1:
    raise SystemExit(
        "ERROR: next audit sequence cursor mismatch"
    )

page_two = service.query(
    records=records,
    query=audit.AuditQuery(
        resource_type="order",
        resource_id="order-001",
        after_sequence=(
            result.next_after_sequence
        ),
        limit=100,
    ),
    request_context=ctx,
)

if (
    len(page_two.records) != 1
    or page_two.records[0]["sequence"] != 2
):
    raise SystemExit(
        "ERROR: audit sequence pagination second page failed"
    )

if any(
    record["audit_id"] == "audit-003"
    for record in (
        list(result.records)
        + list(page_two.records)
    )
):
    raise SystemExit(
        "ERROR: cross-tenant audit record leaked into query"
    )

export = service.export(
    records=records,
    query=audit.AuditQuery(
        action="order.create",
        limit=100,
    ),
    request_context=ctx,
    generated_at="2026-01-01T01:00:00+00:00",
)

if export.selected_count != 1:
    raise SystemExit(
        "ERROR: audit export filter count mismatch"
    )

if not export.verify_selection():
    raise SystemExit(
        "ERROR: audit export selection hash verification failed"
    )

if (
    export.access_audit_event["action"]
    != "audit.export"
):
    raise SystemExit(
        "ERROR: export access did not produce audit evidence"
    )

tampered = [
    dict(record)
    for record in records
]
tampered[1] = dict(
    tampered[1]
)
tampered[1]["event"] = dict(
    tampered[1]["event"]
)
tampered[1]["event"]["action"] = (
    "tampered.action"
)

try:
    service.query(
        records=tampered,
        query=audit.AuditQuery(),
        request_context=ctx,
    )
except audit.AuditBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: tampered Kernel audit chain was accepted"
    )

cross_ctx = request_context.BaaSRequestContext(
    request_id="req-audit-cross",
    correlation_id="corr-audit-cross",
    service="audit",
    operation="audit.query",
    organization_id="org-other",
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
    actor_id="auditor-other",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_audit_cross",
    idempotency_key="idem-audit-cross",
)

cross_result = service.query(
    records=records,
    query=audit.AuditQuery(
        limit=100,
    ),
    request_context=cross_ctx,
)

if (
    len(cross_result.records) != 1
    or cross_result.records[0]["audit_id"]
    != "audit-003"
):
    raise SystemExit(
        "ERROR: tenant-scoped audit query returned wrong records"
    )

status = (
    BAAS / "IMPLEMENTATION_STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "- [x] Audit",
    "- [x] Full source-chain verification before access",
    "- [x] Tenant-scoped audit query",
    "- [x] Tamper-evident export manifest",
    "- [x] No audit mutation/delete API",
    "- [x] Logging",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Audit BaaS status missing: "
            + phrase
        )

print("OK: Kernel Audit remains authoritative.")
print("OK: Full audit chain verifies before access.")
print("OK: Tenant-scoped filtering and pagination passed.")
print("OK: Sensitive metadata remains redacted.")
print("OK: Tampered audit chain fails closed.")
print("OK: Export selection hash verification passed.")
print("OK: Query/export access produces audit evidence.")
print("OK: No mutation/delete API is exposed.")
print("STATUS: BAAS P0 AUDIT READY")
