#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
KERNEL = ROOT / "kernel"

MODULES = {
    "kernel_secrets": KERNEL / "secrets/runtime.py",
    "kernel_backups": KERNEL / "backups/runtime.py",
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Kernel secret/backup runtime file: {path}"
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


secrets = load_module(
    "kernel_secrets",
    MODULES["kernel_secrets"],
)
backups = load_module(
    "kernel_backups",
    MODULES["kernel_backups"],
)

registry = secrets.SecretReferenceRegistry()

descriptor = secrets.SecretDescriptor(
    secret_ref="vault://kernel/validation/database",
    organization_id="org-validation",
    purpose="database-credential",
    owner="Kernel Platform",
    version="1",
    environment_id="env-validation",
    allowed_consumers=[
        "kernel.database",
        "kernel.migrations",
    ],
    metadata={
        "rotation_policy": "managed-externally",
    },
)

registry.register(descriptor)

context = registry.resolve(
    secret_ref=descriptor.secret_ref,
    organization_id="org-validation",
    environment_id="env-validation",
    consumer="kernel.database",
)

if context.secret_ref != descriptor.secret_ref:
    raise SystemExit(
        "ERROR: secret context reference mismatch"
    )

if hasattr(context, "secret_value"):
    raise SystemExit(
        "ERROR: SecretContext exposes raw secret value"
    )

try:
    registry.resolve(
        secret_ref=descriptor.secret_ref,
        organization_id="org-other",
        environment_id="env-validation",
        consumer="kernel.database",
    )
except secrets.SecretReferenceError:
    pass
else:
    raise SystemExit(
        "ERROR: cross-tenant secret reference resolution was accepted"
    )

try:
    registry.resolve(
        secret_ref=descriptor.secret_ref,
        organization_id="org-validation",
        environment_id="env-validation",
        consumer="unknown.consumer",
    )
except secrets.SecretReferenceError:
    pass
else:
    raise SystemExit(
        "ERROR: unauthorized secret consumer was accepted"
    )

bad_descriptor = secrets.SecretDescriptor(
    secret_ref="secret://kernel/validation/bad",
    organization_id="org-validation",
    purpose="validation",
    owner="Kernel Platform",
    version="1",
    environment_id="env-validation",
    allowed_consumers=["kernel.validation"],
    metadata={
        "password": "must-not-store",
    },
)

try:
    registry.register(bad_descriptor)
except secrets.SecretReferenceError:
    pass
else:
    raise SystemExit(
        "ERROR: raw secret-bearing metadata was accepted"
    )

backup_registry = backups.BackupPolicyRegistry()

production_policy = backups.BackupPolicy(
    policy_id="kernel-postgres-production",
    resource_class="postgresql",
    environment_type="PRODUCTION",
    encrypted=True,
    retention_days=35,
    frequency_minutes=15,
    rpo_minutes=15,
    rto_minutes=60,
    immutable_copy=True,
    offsite_copy=True,
    restore_test_interval_days=30,
    metadata={
        "owner": "Kernel Platform",
    },
)

backup_registry.register(production_policy)

if backup_registry.trusted_for_recovery(
    production_policy.policy_id
):
    raise SystemExit(
        "ERROR: untested backup policy was trusted for recovery"
    )

verification = backups.RestoreVerification(
    verification_id="restore-validation-001",
    policy_id=production_policy.policy_id,
    backup_reference="backup://validation/postgres/001",
    tested_at="2026-01-01T00:00:00+00:00",
    success=True,
    restored_resource_reference=(
        "restore://validation/postgres/001"
    ),
    checksum_verified=True,
    notes="validation restore",
)

backup_registry.record_restore_verification(
    verification
)

if not backup_registry.trusted_for_recovery(
    production_policy.policy_id
):
    raise SystemExit(
        "ERROR: successfully verified backup was not trusted"
    )

bad_production = backups.BackupPolicy(
    policy_id="kernel-postgres-invalid",
    resource_class="postgresql",
    environment_type="PRODUCTION",
    encrypted=False,
    retention_days=7,
    frequency_minutes=60,
    rpo_minutes=60,
    rto_minutes=120,
    immutable_copy=False,
    offsite_copy=False,
    restore_test_interval_days=30,
)

try:
    bad_production.validate()
except backups.BackupContractError:
    pass
else:
    raise SystemExit(
        "ERROR: unsafe production backup policy was accepted"
    )

bad_rpo = backups.BackupPolicy(
    policy_id="kernel-rpo-invalid",
    resource_class="postgresql",
    environment_type="DEVELOPMENT",
    encrypted=False,
    retention_days=1,
    frequency_minutes=60,
    rpo_minutes=120,
    rto_minutes=120,
    immutable_copy=False,
    offsite_copy=False,
    restore_test_interval_days=30,
)

try:
    bad_rpo.validate()
except backups.BackupContractError:
    pass
else:
    raise SystemExit(
        "ERROR: RPO exceeding backup frequency was accepted"
    )

status = (
    KERNEL / "IMPLEMENTATION_STATUS.md"
).read_text(encoding="utf-8")

for phrase in [
    "- [x] Secret reference boundary",
    "- [x] Backup contract",
    "- [ ] PostgreSQL persistence boundary",
    "- [ ] Migration framework",
    "- [ ] Commerce primitives",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Kernel P0 status missing: " + phrase
        )

print("OK: Secret references are tenant/environment scoped.")
print("OK: Unauthorized secret consumers fail closed.")
print("OK: Raw secret-bearing metadata is rejected.")
print("OK: Production backup safety policy validation passed.")
print("OK: Untested backups are not trusted for recovery.")
print("OK: Restore verification produces trusted recovery evidence.")
print("OK: PostgreSQL + migration P0 requirements remain visible.")
print("STATUS: KERNEL P0 SECRETS + BACKUPS READY")
