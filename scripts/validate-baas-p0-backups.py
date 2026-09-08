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
    "baas_backups": (
        BAAS / "backups/runtime.py"
    ),
    "kernel_backups": (
        KERNEL / "backups/runtime.py"
    ),
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Backups runtime file: {path}"
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
backups = load_module(
    "baas_backups",
    MODULES["baas_backups"],
)
kernel_backups = load_module(
    "kernel_backups",
    MODULES["kernel_backups"],
)

ctx = request_context.BaaSRequestContext(
    request_id="req-backups-validation",
    correlation_id="corr-backups-validation",
    service="backups",
    operation="backups.plan",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="SERVICE_ACCOUNT",
    kernel_authorization_ref="kernel_auth_backups_validation",
    idempotency_key="idem-backups-validation",
)
ctx.validate()

registry = kernel_backups.BackupPolicyRegistry()

service = backups.BackupsService(
    kernel_registry=registry,
    kernel_policy_type=(
        kernel_backups.BackupPolicy
    ),
    kernel_restore_verification_type=(
        kernel_backups.RestoreVerification
    ),
)

provider = backups.BackupProvider(
    provider_id="backup_primary",
    adapter_ref="adapter://backups/primary",
    credential_ref="vault://backups/primary/control",
    supports_encryption=True,
    supports_immutable_copy=True,
    supports_offsite_copy=True,
    supports_restore=True,
)

service.register_provider(
    provider=provider,
    request_context=ctx,
)

tenant = backups.TenantScope(
    organization_id=ctx.organization_id,
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
)

policy = backups.TenantBackupPolicy(
    policy_id="backup-policy-database-production",
    tenant=tenant,
    resource_class="DATABASE",
    resource_ref="database://primary",
    environment_type="PRODUCTION",
    provider_id=provider.provider_id,
    encrypted=True,
    retention_days=35,
    frequency_minutes=60,
    rpo_minutes=60,
    rto_minutes=120,
    immutable_copy=True,
    offsite_copy=True,
    restore_test_interval_days=30,
    enabled=True,
    metadata={
        "tier": "critical",
    },
)

registered = service.register_policy(
    policy=policy,
    request_context=ctx,
)

if (
    registered["policy"].environment_type
    != "PRODUCTION"
):
    raise SystemExit(
        "ERROR: production backup policy registration failed"
    )

if not service.backup_due(
    policy_id=policy.policy_id,
    request_context=ctx,
    now="2026-09-08T22:00:00+00:00",
):
    raise SystemExit(
        "ERROR: new backup policy was not immediately due"
    )

plan = service.plan_backup(
    policy_id=policy.policy_id,
    request_context=ctx,
    requested_at="2026-09-08T22:00:00+00:00",
)

if (
    plan.state
    != "READY_FOR_BACKUP_ADAPTER"
):
    raise SystemExit(
        "ERROR: BaaS Backups claimed provider execution"
    )

if not plan.provider_credential_ref.startswith(
    "vault://"
):
    raise SystemExit(
        "ERROR: backup provider credentials are not reference-only"
    )

evidence = backups.BackupEvidence(
    backup_id=plan.backup_id,
    policy_id=policy.policy_id,
    backup_reference=(
        "provider-backup://primary/db/20260908T220000Z"
    ),
    checksum_sha256=("a" * 64),
    started_at="2026-09-08T22:00:00+00:00",
    completed_at="2026-09-08T22:05:00+00:00",
    encrypted=True,
    immutable_copy=True,
    offsite_copy=True,
    success=True,
)

recorded = service.record_backup_evidence(
    evidence=evidence,
    request_context=ctx,
)

if not recorded["created"]:
    raise SystemExit(
        "ERROR: valid backup evidence was not created"
    )

if service.backup_due(
    policy_id=policy.policy_id,
    request_context=ctx,
    now="2026-09-08T22:59:59+00:00",
):
    raise SystemExit(
        "ERROR: backup became due before configured frequency"
    )

if not service.backup_due(
    policy_id=policy.policy_id,
    request_context=ctx,
    now="2026-09-08T23:05:00+00:00",
):
    raise SystemExit(
        "ERROR: backup due calculation failed"
    )

try:
    service.record_backup_evidence(
        evidence=backups.BackupEvidence(
            backup_id="backup-insecure",
            policy_id=policy.policy_id,
            backup_reference=(
                "backup://insecure"
            ),
            checksum_sha256=("b" * 64),
            started_at="2026-09-08T23:05:00+00:00",
            completed_at="2026-09-08T23:06:00+00:00",
            encrypted=False,
            immutable_copy=True,
            offsite_copy=True,
            success=True,
        ),
        request_context=ctx,
    )
except backups.BackupsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: unencrypted production backup evidence was accepted"
    )

try:
    backups.BackupEvidence(
        backup_id="backup-naive",
        policy_id=policy.policy_id,
        backup_reference=(
            "backup://naive"
        ),
        checksum_sha256=("c" * 64),
        started_at="2026-09-08T22:00:00",
        completed_at="2026-09-08T22:05:00",
        encrypted=True,
        immutable_copy=True,
        offsite_copy=True,
        success=True,
    ).validate()
except backups.BackupsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: timezone-naive backup evidence was accepted"
    )

restore_test = service.plan_restore_test(
    backup_id=evidence.backup_id,
    target_ref="database://restore-validation",
    request_context=ctx,
    requested_at="2026-09-09T00:00:00+00:00",
)

if (
    restore_test.state
    != "READY_FOR_RESTORE_TEST_ADAPTER"
):
    raise SystemExit(
        "ERROR: restore test plan claimed restore execution"
    )

verification = backups.RestoreEvidence(
    verification_id="restore-verification-001",
    policy_id=policy.policy_id,
    backup_id=evidence.backup_id,
    backup_reference=(
        evidence.backup_reference
    ),
    tested_at="2026-09-09T00:10:00+00:00",
    success=True,
    restored_resource_reference=(
        "database://restore-validation"
    ),
    checksum_verified=True,
    notes="Restore verified successfully.",
)

service.record_restore_verification(
    evidence=verification,
    request_context=ctx,
)

if not registry.trusted_for_recovery(
    policy.policy_id
):
    raise SystemExit(
        "ERROR: Kernel recovery trust did not accept successful verification"
    )

if not service.trusted_for_recovery(
    policy_id=policy.policy_id,
    request_context=ctx,
    now="2026-10-09T00:10:00+00:00",
):
    raise SystemExit(
        "ERROR: restore trust expired too early"
    )

if service.trusted_for_recovery(
    policy_id=policy.policy_id,
    request_context=ctx,
    now="2026-10-09T00:10:01+00:00",
):
    raise SystemExit(
        "ERROR: stale restore verification remained trusted"
    )

restore = service.plan_restore(
    backup_id=evidence.backup_id,
    target_ref="database://disaster-recovery",
    request_context=ctx,
    requested_at="2026-10-01T00:00:00+00:00",
)

if (
    restore.state
    != "READY_FOR_RESTORE_ADAPTER"
):
    raise SystemExit(
        "ERROR: restore plan claimed provider execution"
    )

if (
    restore.rpo_minutes != 60
    or restore.rto_minutes != 120
):
    raise SystemExit(
        "ERROR: RPO/RTO policy was not preserved"
    )

try:
    backups.RestoreEvidence(
        verification_id="restore-secret-notes",
        policy_id=policy.policy_id,
        backup_id=evidence.backup_id,
        backup_reference=(
            evidence.backup_reference
        ),
        tested_at="2026-09-09T00:10:00+00:00",
        success=True,
        restored_resource_reference=(
            "database://restore-validation"
        ),
        checksum_verified=True,
        notes="password=must-not-appear",
    ).validate()
except backups.BackupsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: secret-bearing restore notes were accepted"
    )

cross_ctx = request_context.BaaSRequestContext(
    request_id="req-backups-cross",
    correlation_id="corr-backups-cross",
    service="backups",
    operation="backups.restore",
    organization_id="org-other",
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
    actor_id="actor-other",
    actor_type="SERVICE_ACCOUNT",
    kernel_authorization_ref="kernel_auth_backups_cross",
    idempotency_key="idem-backups-cross",
)

try:
    service.backup_due(
        policy_id=policy.policy_id,
        request_context=cross_ctx,
        now="2026-09-09T00:00:00+00:00",
    )
except backups.BackupsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: cross-tenant backup access was accepted"
    )

try:
    backups.BackupProvider(
        provider_id="bad_provider",
        adapter_ref="adapter://bad",
        credential_ref="raw-password",
        supports_encryption=True,
        supports_immutable_copy=True,
        supports_offsite_copy=True,
        supports_restore=True,
    ).validate()
except backups.BackupsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: raw backup provider credential was accepted"
    )

try:
    backups.TenantBackupPolicy(
        policy_id="bad-production-policy",
        tenant=tenant,
        resource_class="DATABASE",
        resource_ref="database://bad",
        environment_type="PRODUCTION",
        provider_id=provider.provider_id,
        encrypted=True,
        retention_days=30,
        frequency_minutes=60,
        rpo_minutes=60,
        rto_minutes=120,
        immutable_copy=False,
        offsite_copy=True,
        restore_test_interval_days=30,
        enabled=True,
        metadata={},
    ).validate()
except backups.BackupsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: production policy without immutable copy was accepted"
    )

status = (
    BAAS / "IMPLEMENTATION_STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "- [x] Backups",
    "- [x] Restore-test staleness enforcement",
    "- [x] Trusted recovery gate",
    "DALIZEBO BAAS P0: COMPLETE",
    "Phase 6 — Commerce + POS foundation.",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: BaaS Phase 5 closure status missing: "
            + phrase
        )

print("OK: Kernel Backup authority remains canonical.")
print("OK: Production encryption/immutable/offsite policy passed.")
print("OK: Backup due scheduling metadata passed.")
print("OK: Provider credentials remain opaque secret references.")
print("OK: Timezone-aware backup evidence and checksum rules passed.")
print("OK: Restore testing records through Kernel registry.")
print("OK: Restore-test staleness hardening passed.")
print("OK: Trusted recovery gate and RPO/RTO propagation passed.")
print("OK: Cross-tenant backup access fails closed.")
print("STATUS: BAAS P0 BACKUPS READY")
print("STATUS: DALIZEBO BAAS P0 COMPLETE")
