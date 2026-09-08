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
    "baas_secrets": (
        BAAS / "secrets/runtime.py"
    ),
    "kernel_secrets": (
        KERNEL / "secrets/runtime.py"
    ),
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Secrets runtime file: {path}"
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
secrets_baas = load_module(
    "baas_secrets",
    MODULES["baas_secrets"],
)
kernel_secrets = load_module(
    "kernel_secrets",
    MODULES["kernel_secrets"],
)

ctx = request_context.BaaSRequestContext(
    request_id="req-secrets-validation",
    correlation_id="corr-secrets-validation",
    service="secrets",
    operation="secrets.register",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="SERVICE_ACCOUNT",
    kernel_authorization_ref="kernel_auth_secrets_validation",
    idempotency_key="idem-secrets-validation",
)
ctx.validate()

registry = kernel_secrets.SecretReferenceRegistry()
service = secrets_baas.SecretsService(
    kernel_registry=registry,
    kernel_descriptor_type=(
        kernel_secrets.SecretDescriptor
    ),
)

provider = secrets_baas.SecretProvider(
    provider_id="vault_primary",
    adapter_ref="adapter://secrets/vault-primary",
    control_credential_ref="kms://platform/vault-control",
    encryption_at_rest_required=True,
    supports_rotation=True,
)

service.register_provider(
    provider=provider,
    request_context=ctx,
)

tenant = secrets_baas.TenantScope(
    organization_id=ctx.organization_id,
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
)

registration = secrets_baas.SecretRegistration(
    secret_id="secret-database-primary",
    tenant=tenant,
    name="Primary Database Credential",
    purpose="database connectivity",
    owner="database",
    provider_id=provider.provider_id,
    secret_ref="vault://database/primary/v1",
    version="1",
    allowed_consumers=(
        "database",
        "backups",
    ),
    rotation_interval_days=30,
    rotated_at="2026-09-01T00:00:00+00:00",
    state="ACTIVE",
    metadata={
        "classification": "credential",
    },
)

registered = service.register_secret(
    registration=registration,
    request_context=ctx,
)

if (
    registered["provider_policy"][
        "encryption_at_rest_required"
    ]
    is not True
):
    raise SystemExit(
        "ERROR: encryption-at-rest provider requirement was lost"
    )

kernel_descriptor = registry.get(
    registration.secret_ref
)

if (
    kernel_descriptor.organization_id
    != ctx.organization_id
    or kernel_descriptor.environment_id
    != ctx.environment_id
):
    raise SystemExit(
        "ERROR: Kernel secret registration scope mismatch"
    )

access = service.access_plan(
    secret_id=registration.secret_id,
    consumer="database",
    request_context=ctx,
    accessed_at="2026-09-08T22:00:00+00:00",
)

if (
    access.state
    != "READY_FOR_SECRET_MANAGER_ADAPTER"
):
    raise SystemExit(
        "ERROR: Secrets BaaS claimed raw retrieval"
    )

if access.secret_ref != registration.secret_ref:
    raise SystemExit(
        "ERROR: reference-only access changed secret reference"
    )

if hasattr(
    access,
    "secret_value",
):
    raise SystemExit(
        "ERROR: access plan exposes secret_value"
    )

try:
    service.access_plan(
        secret_id=registration.secret_id,
        consumer="unauthorized-service",
        request_context=ctx,
    )
except Exception:
    pass
else:
    raise SystemExit(
        "ERROR: unauthorized secret consumer was accepted"
    )

if service.rotation_due(
    secret_id=registration.secret_id,
    request_context=ctx,
    now="2026-09-30T23:59:59+00:00",
):
    raise SystemExit(
        "ERROR: secret rotation became due too early"
    )

if not service.rotation_due(
    secret_id=registration.secret_id,
    request_context=ctx,
    now="2026-10-01T00:00:00+00:00",
):
    raise SystemExit(
        "ERROR: secret rotation due calculation failed"
    )

rotation = service.plan_rotation(
    secret_id=registration.secret_id,
    next_version="2",
    request_context=ctx,
    planned_at="2026-10-01T00:00:00+00:00",
)

if (
    rotation.state
    != "READY_FOR_SECRET_MANAGER_ROTATION_ADAPTER"
):
    raise SystemExit(
        "ERROR: rotation plan claimed external rotation"
    )

if not rotation.provider_control_credential_ref.startswith(
    "kms://"
):
    raise SystemExit(
        "ERROR: provider control credential is not reference-only"
    )

confirmed = service.confirm_rotation(
    rotation_plan=rotation,
    new_secret_ref="vault://database/primary/v2",
    rotated_at="2026-10-01T00:00:05+00:00",
    request_context=ctx,
)

if confirmed["registration"].version != "2":
    raise SystemExit(
        "ERROR: secret rotation version was not advanced"
    )

try:
    registry.resolve(
        secret_ref="vault://database/primary/v1",
        organization_id=ctx.organization_id,
        environment_id=ctx.environment_id,
        consumer="database",
    )
except Exception:
    pass
else:
    raise SystemExit(
        "ERROR: old secret reference remained enabled after rotation"
    )

rotated_access = service.access_plan(
    secret_id=registration.secret_id,
    consumer="database",
    request_context=ctx,
    accessed_at="2026-10-01T00:01:00+00:00",
)

if (
    rotated_access.secret_ref
    != "vault://database/primary/v2"
    or rotated_access.descriptor_version
    != "2"
):
    raise SystemExit(
        "ERROR: rotated secret access plan did not use new descriptor"
    )

disabled = service.disable(
    secret_id=registration.secret_id,
    request_context=ctx,
    disabled_at="2026-10-02T00:00:00+00:00",
)

if disabled["registration"].state != "DISABLED":
    raise SystemExit(
        "ERROR: BaaS secret disablement failed"
    )

try:
    service.access_plan(
        secret_id=registration.secret_id,
        consumer="database",
        request_context=ctx,
    )
except secrets_baas.SecretsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: disabled secret remained accessible"
    )

cross_ctx = request_context.BaaSRequestContext(
    request_id="req-secrets-cross",
    correlation_id="corr-secrets-cross",
    service="secrets",
    operation="secrets.access",
    organization_id="org-other",
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
    actor_id="actor-other",
    actor_type="SERVICE_ACCOUNT",
    kernel_authorization_ref="kernel_auth_secrets_cross",
    idempotency_key="idem-secrets-cross",
)

try:
    service.rotation_due(
        secret_id=registration.secret_id,
        request_context=cross_ctx,
        now="2026-10-03T00:00:00+00:00",
    )
except secrets_baas.SecretsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: cross-tenant secret access was accepted"
    )

try:
    secrets_baas.SecretProvider(
        provider_id="bad_provider",
        adapter_ref="adapter://bad",
        control_credential_ref="raw-provider-password",
        encryption_at_rest_required=True,
        supports_rotation=True,
    ).validate()
except secrets_baas.SecretsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: raw provider credential was accepted"
    )

try:
    secrets_baas.SecretRegistration(
        secret_id="secret-bad-metadata",
        tenant=tenant,
        name="Bad",
        purpose="test",
        owner="test",
        provider_id=provider.provider_id,
        secret_ref="vault://test/bad",
        version="1",
        allowed_consumers=("database",),
        rotation_interval_days=None,
        rotated_at="2026-09-01T00:00:00+00:00",
        state="ACTIVE",
        metadata={
            "api_key": "must-not-store"
        },
    ).validate()
except secrets_baas.SecretsBaaSError:
    pass
else:
    raise SystemExit(
        "ERROR: secret-bearing metadata was accepted"
    )

status = (
    BAAS / "IMPLEMENTATION_STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "- [x] Secrets",
    "- [x] Kernel Secret Reference authority boundary",
    "- [x] Reference-only access planning",
    "- [x] Rotation confirmation with old-reference disablement",
    "- [x] No secret-value field/API",
    "- [ ] Backups",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Secrets status missing: "
            + phrase
        )

print("OK: Kernel Secret Reference authority remains canonical.")
print("OK: Full tenant/environment secret scope passed.")
print("OK: Secret-manager providers require opaque control credentials and encryption policy.")
print("OK: Consumer allowlists fail closed.")
print("OK: Access plans expose references only, never secret values.")
print("OK: Rotation due/planning/confirmation passed.")
print("OK: Old reference is disabled after confirmed rotation.")
print("OK: Secret disablement and cross-tenant isolation passed.")
print("STATUS: BAAS P0 SECRETS READY")
