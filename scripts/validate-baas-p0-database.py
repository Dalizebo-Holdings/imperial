#!/usr/bin/env python3

from __future__ import annotations

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
    "baas_database": (
        BAAS / "database/runtime.py"
    ),
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Database BaaS runtime file: {path}"
        )
    py_compile.compile(
        str(path),
        doraise=True,
    )


def load_module(name: str, path: Path):
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
database = load_module(
    "baas_database",
    MODULES["baas_database"],
)

ctx = request_context.BaaSRequestContext(
    request_id="req-db-validation",
    correlation_id="corr-db-validation",
    service="database",
    operation="database.manage",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_db_validation",
    idempotency_key="idem-db-validation",
)
ctx.validate()

tenant = database.TenantScope(
    organization_id=ctx.organization_id,
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
    environment_type="PRODUCTION",
)

policy = database.ConnectionPolicy(
    max_connections=50,
    connect_timeout_seconds=10,
    statement_timeout_ms=30000,
    idle_transaction_timeout_ms=30000,
    ssl_mode="verify-full",
)

managed = database.ManagedDatabase(
    database_id="db-validation",
    tenant=tenant,
    name="Validation Database",
    engine="PostgreSQL",
    engine_version="17",
    dsn_ref="vault://baas/validation/postgres",
    schema="public",
    state="PROVISIONING",
    connection_policy=policy,
    backup_policy_ref=None,
    created_at="2026-01-01T00:00:00+00:00",
    updated_at="2026-01-01T00:00:00+00:00",
)

manager = database.TenantDatabaseManager()
manager.register(
    database=managed,
    request_context=ctx,
)

try:
    manager.transition(
        database_id=managed.database_id,
        target_state="READY",
        request_context=ctx,
        now="2026-01-01T00:00:01+00:00",
    )
except database.DatabaseBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: production database became READY without backup policy"
    )

ready = manager.transition(
    database_id=managed.database_id,
    target_state="READY",
    request_context=ctx,
    backup_policy_ref="backup-policy://validation",
    now="2026-01-01T00:00:01+00:00",
)

if ready.state != "READY":
    raise SystemExit(
        "ERROR: database did not transition to READY"
    )

plan = manager.connection_plan(
    database_id=managed.database_id,
    request_context=ctx,
)

if plan["dsn_ref"] != managed.dsn_ref:
    raise SystemExit(
        "ERROR: connection plan changed opaque DSN reference"
    )

if "password" in str(plan).lower():
    raise SystemExit(
        "ERROR: connection plan exposed password material"
    )

cross_tenant = request_context.BaaSRequestContext(
    request_id="req-db-cross",
    correlation_id="corr-db-cross",
    service="database",
    operation="database.read",
    organization_id="org-other",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_cross",
    idempotency_key="idem-cross",
)

try:
    manager.get(
        database_id=managed.database_id,
        request_context=cross_tenant,
    )
except database.DatabaseBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: cross-tenant database access was accepted"
    )

migration = database.MigrationIntent(
    migration_id="mig-validation-001",
    database_id=managed.database_id,
    version=1,
    checksum="a" * 64,
    description="validation migration",
    transactional=True,
    reversible=True,
    rollback_reference="migration://rollback/001",
    requested_at="2026-01-01T00:00:02+00:00",
)

manager.record_migration_intent(
    intent=migration,
    request_context=ctx,
)

try:
    manager.record_migration_intent(
        intent=database.MigrationIntent(
            migration_id="mig-validation-conflict",
            database_id=managed.database_id,
            version=1,
            checksum="b" * 64,
            description="checksum conflict",
            transactional=True,
            reversible=True,
            rollback_reference="migration://rollback/001",
            requested_at="2026-01-01T00:00:03+00:00",
        ),
        request_context=ctx,
    )
except database.DatabaseBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: migration checksum conflict was accepted"
    )

restore = database.RestoreIntent(
    restore_id="restore-validation-001",
    database_id=managed.database_id,
    backup_reference="backup://validation/001",
    target_environment_id=ctx.environment_id,
    requested_at="2026-01-01T00:00:04+00:00",
)

manager.record_restore_intent(
    intent=restore,
    request_context=ctx,
)

manager.observe_query(
    observation=database.QueryObservation(
        database_id=managed.database_id,
        correlation_id=ctx.correlation_id,
        operation="SELECT",
        duration_ms=12.5,
        row_count=1,
        success=True,
    ),
    request_context=ctx,
)

status = (
    BAAS / "IMPLEMENTATION_STATUS.md"
).read_text(encoding="utf-8")

for phrase in [
    "- [x] PostgreSQL Database BaaS",
    "- [x] Tenant database manager",
    "- [x] Migration intent validation",
    "- [x] Restore intent validation",
    "- [x] Query observation contract",
    "- [ ] Object Storage",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: BaaS status missing: "
            + phrase
        )

print("OK: Tenant database registration passed.")
print("OK: Production READY state requires backup policy.")
print("OK: Connection planning exposes references only.")
print("OK: Cross-tenant database access fails closed.")
print("OK: Migration checksum conflict fails closed.")
print("OK: Restore intent validation passed.")
print("OK: Query observation contract passed.")
print("STATUS: BAAS P0 DATABASE READY")
