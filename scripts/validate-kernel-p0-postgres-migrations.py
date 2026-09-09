#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KERNEL = ROOT / "kernel"

MODULES = {
    "kernel_postgres": KERNEL / "persistence/runtime.py",
    "kernel_migrations": KERNEL / "migrations/runtime.py",
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Kernel persistence runtime file: {path}"
        )
    py_compile.compile(str(path), doraise=True)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)

    if spec is None or spec.loader is None:
        raise SystemExit(
            f"ERROR: unable to load module: {path}"
        )

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


postgres = load_module(
    "kernel_postgres",
    MODULES["kernel_postgres"],
)
migrations = load_module(
    "kernel_migrations",
    MODULES["kernel_migrations"],
)

prod = postgres.PostgresConfig(
    dsn_ref="vault://kernel/production/postgres",
    environment_type="PRODUCTION",
    application_name="dalizebo-kernel",
    schema="kernel",
    ssl_mode="verify-full",
    connect_timeout_seconds=10,
    statement_timeout_ms=30000,
    idle_transaction_timeout_ms=30000,
)
prod.validate()

raw_dsn_rejected = False
try:
    postgres.PostgresConfig(
        dsn_ref="postgresql://user:password@db/kernel",
        environment_type="PRODUCTION",
        ssl_mode="verify-full",
    ).validate()
except postgres.PostgresBoundaryError:
    raw_dsn_rejected = True
if not raw_dsn_rejected:
    raise SystemExit(
        "ERROR: raw PostgreSQL DSN credentials were accepted"
    )

weak_tls_rejected = False
try:
    postgres.PostgresConfig(
        dsn_ref="secret://kernel/prod/postgres",
        environment_type="PRODUCTION",
        ssl_mode="require",
    ).validate()
except postgres.PostgresBoundaryError:
    weak_tls_rejected = True
if not weak_tls_rejected:
    raise SystemExit(
        "ERROR: production PostgreSQL accepted ssl_mode below verify-full"
    )

tenant = postgres.TenantSessionContext(
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    correlation_id="corr-validation",
)

prelude = postgres.transaction_prelude(
    config=prod,
    tenant=tenant,
)

if prelude[0][0] != "BEGIN":
    raise SystemExit(
        "ERROR: PostgreSQL transaction prelude does not begin with BEGIN"
    )

joined = "\n".join(statement for statement, _ in prelude)

for required in [
    "app.organization_id",
    "app.workspace_id",
    "app.project_id",
    "app.environment_id",
    "app.actor_id",
    "app.correlation_id",
]:
    if required not in joined:
        raise SystemExit(
            "ERROR: tenant transaction context missing: " + required
        )

sql_dir = KERNEL / "migrations/sql"
available = migrations.discover_migrations(sql_dir)

if available[0].version != 1:
    raise SystemExit(
        "ERROR: baseline migration version is not 0001"
    )

if migrations.plan_migrations(
    available=available,
    applied=[],
) != available:
    raise SystemExit(
        "ERROR: fresh database migration plan is incomplete"
    )

applied = [
    migrations.AppliedMigration(
        version=available[0].version,
        name=available[0].name,
        checksum=available[0].checksum,
    )
]

remaining = migrations.plan_migrations(
    available=available,
    applied=applied,
)
if remaining != available[1:]:
    raise SystemExit(
        "ERROR: remaining migration plan is incorrect"
    )

all_applied = [
    migrations.AppliedMigration(
        version=migration.version,
        name=migration.name,
        checksum=migration.checksum,
    )
    for migration in available
]
if migrations.plan_migrations(
    available=available,
    applied=all_applied,
):
    raise SystemExit(
        "ERROR: fully-applied migrations were planned again"
    )

checksum_drift_rejected = False
try:
    migrations.plan_migrations(
        available=available,
        applied=[
            migrations.AppliedMigration(
                version=1,
                name=available[0].name,
                checksum="0" * 64,
            )
        ],
    )
except migrations.MigrationError:
    checksum_drift_rejected = True
if not checksum_drift_rejected:
    raise SystemExit(
        "ERROR: migration checksum drift was accepted"
    )

baseline = (
    KERNEL / "migrations/sql/0001_kernel_foundation.sql"
).read_text(encoding="utf-8")

required_tables = [
    "kernel.schema_migrations",
    "kernel.organizations",
    "kernel.workspaces",
    "kernel.projects",
    "kernel.environments",
    "kernel.idempotency_records",
    "kernel.audit_records",
    "kernel.outbox_events",
]

for table in required_tables:
    if table not in baseline:
        raise SystemExit(
            "ERROR: baseline migration missing table: " + table
        )

for required_token in [
    "organization_id",
    "correlation_id",
    "request_hash",
    "record_hash",
    "published_at",
]:
    if required_token not in baseline:
        raise SystemExit(
            "ERROR: baseline migration missing field: "
            + required_token
        )

lower = baseline.lower()
for forbidden in [
    "password=",
    "api_key=",
    "access_token=",
    "postgresql://",
]:
    if forbidden in lower:
        raise SystemExit(
            "ERROR: migration contains forbidden secret material: "
            + forbidden
        )

status = (
    KERNEL / "IMPLEMENTATION_STATUS.md"
).read_text(encoding="utf-8")

for phrase in [
    "- [x] PostgreSQL persistence boundary",
    "- [x] Migration framework",
    "- [x] Commerce primitives",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Kernel P0 status missing: " + phrase
        )

print("OK: PostgreSQL config accepts secret references only.")
print("OK: Production PostgreSQL requires verify-full TLS.")
print("OK: Tenant transaction-local context contract passed.")
print("OK: Baseline migration discovery and ordering passed.")
print("OK: Applied migration checksum verification passed.")
print("OK: Migration checksum drift fails closed.")
print("OK: Baseline Kernel schema contains required P0 tables.")
print("OK: Baseline migration contains no embedded credentials.")
print("STATUS: KERNEL P0 POSTGRESQL + MIGRATIONS READY")
