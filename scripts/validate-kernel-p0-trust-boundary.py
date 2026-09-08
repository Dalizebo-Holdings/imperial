#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
KERNEL = ROOT / "kernel"

MODULES = {
    "identity_context": KERNEL / "identity/context.py",
    "tenant_context": KERNEL / "tenancy/context.py",
    "kernel_authorization": KERNEL / "authorization/runtime.py",
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Kernel runtime file: {path}"
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


identity_context = load_module(
    "identity_context",
    MODULES["identity_context"],
)
tenant_context = load_module(
    "tenant_context",
    MODULES["tenant_context"],
)
kernel_authorization = load_module(
    "kernel_authorization",
    MODULES["kernel_authorization"],
)

identity = identity_context.IdentityContext(
    actor_id="actor-validation",
    actor_type="HUMAN_USER",
    authenticated=True,
    authentication_method="PASSKEY",
    identity_ref="identity://validation/actor",
    mfa_verified=True,
    attributes={"source": "validation"},
)
identity.validate()

tenant = tenant_context.TenantContext(
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    environment_type="DEVELOPMENT",
    actor_id="actor-validation",
    actor_type="HUMAN_USER",
    correlation_id="corr-validation",
    verified=True,
    verification_source="server-side-membership-resolution",
)
tenant.validate_identity(identity)

permissions = kernel_authorization.PermissionRegistry()

for permission in [
    kernel_authorization.PermissionDefinition(
        permission_id="orders.read",
        description="Read orders",
    ),
    kernel_authorization.PermissionDefinition(
        permission_id="kernel.cross_tenant",
        description="Explicit privileged cross-tenant Kernel access",
        sensitive=True,
    ),
]:
    permissions.register(permission)

roles = kernel_authorization.RoleRegistry()

roles.register(
    kernel_authorization.RoleDefinition(
        role_id="role-validation-reader",
        permissions=frozenset({"orders.read"}),
        organization_id="org-validation",
        workspace_id="workspace-validation",
        project_id="project-validation",
        environment_id="env-validation",
    )
)

allow_request = kernel_authorization.AuthorizationRequest(
    decision_request_id="decision-validation-allow",
    identity=identity,
    tenant=tenant,
    role_id="role-validation-reader",
    required_permission="orders.read",
    resource_scope="orders/*",
    policy_outcome="ALLOW",
)

allow_one = kernel_authorization.authorize(
    request=allow_request,
    permissions=permissions,
    roles=roles,
)
allow_two = kernel_authorization.authorize(
    request=allow_request,
    permissions=permissions,
    roles=roles,
)

if not allow_one.authorized:
    raise SystemExit(
        "ERROR: valid Kernel authorization was denied: "
        + allow_one.reason
    )

if allow_one.authorization_ref != allow_two.authorization_ref:
    raise SystemExit(
        "ERROR: Kernel authorization reference is not deterministic"
    )

deny_policy = kernel_authorization.AuthorizationRequest(
    decision_request_id="decision-validation-deny",
    identity=identity,
    tenant=tenant,
    role_id="role-validation-reader",
    required_permission="orders.read",
    resource_scope="orders/*",
    policy_outcome="DENY",
)

deny_decision = kernel_authorization.authorize(
    request=deny_policy,
    permissions=permissions,
    roles=roles,
)

if deny_decision.authorized:
    raise SystemExit(
        "ERROR: upstream policy DENY was bypassed"
    )

unverified_tenant = tenant_context.TenantContext(
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    environment_type="DEVELOPMENT",
    actor_id="actor-validation",
    actor_type="HUMAN_USER",
    correlation_id="corr-unverified",
    verified=False,
    verification_source="client-header",
)

unverified_request = kernel_authorization.AuthorizationRequest(
    decision_request_id="decision-validation-unverified",
    identity=identity,
    tenant=unverified_tenant,
    role_id="role-validation-reader",
    required_permission="orders.read",
    resource_scope="orders/*",
    policy_outcome="ALLOW",
)

unverified_decision = kernel_authorization.authorize(
    request=unverified_request,
    permissions=permissions,
    roles=roles,
)

if unverified_decision.authorized:
    raise SystemExit(
        "ERROR: unverified tenant context was authorized"
    )

cross_tenant_request = kernel_authorization.AuthorizationRequest(
    decision_request_id="decision-validation-cross-tenant",
    identity=identity,
    tenant=tenant,
    role_id="role-validation-reader",
    required_permission="orders.read",
    resource_scope="orders/*",
    policy_outcome="ALLOW",
    target_organization_id="org-other",
    privileged=False,
)

cross_tenant_denied = kernel_authorization.authorize(
    request=cross_tenant_request,
    permissions=permissions,
    roles=roles,
)

if cross_tenant_denied.authorized:
    raise SystemExit(
        "ERROR: non-privileged cross-tenant request was authorized"
    )

roles.register(
    kernel_authorization.RoleDefinition(
        role_id="role-validation-privileged",
        permissions=frozenset({
            "orders.read",
            "kernel.cross_tenant",
        }),
        organization_id="org-validation",
        workspace_id="workspace-validation",
        project_id="project-validation",
        environment_id="env-validation",
    )
)

privileged_request = kernel_authorization.AuthorizationRequest(
    decision_request_id="decision-validation-privileged",
    identity=identity,
    tenant=tenant,
    role_id="role-validation-privileged",
    required_permission="orders.read",
    resource_scope="orders/*",
    policy_outcome="ALLOW",
    target_organization_id="org-other",
    privileged=True,
)

privileged_decision = kernel_authorization.authorize(
    request=privileged_request,
    permissions=permissions,
    roles=roles,
)

if not privileged_decision.authorized:
    raise SystemExit(
        "ERROR: explicitly privileged cross-tenant request was denied: "
        + privileged_decision.reason
    )

status = (
    KERNEL / "IMPLEMENTATION_STATUS.md"
).read_text(encoding="utf-8")

for phrase in [
    "- [x] Identity context contract",
    "- [x] Verified tenant context",
    "- [x] Permission registry",
    "- [x] Role registry",
    "- [x] RBAC permission evaluation",
    "- [x] Policy outcome gate",
    "- [x] Cross-tenant privileged access rule",
    "- [x] Deterministic authorization reference",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Kernel P0 status missing: " + phrase
        )

print("OK: Authenticated identity context validation passed.")
print("OK: Verified tenant context validation passed.")
print("OK: RBAC permission evaluation passed.")
print("OK: Upstream policy DENY fails closed.")
print("OK: Unverified tenant context fails closed.")
print("OK: Cross-tenant access requires explicit privilege.")
print("OK: Deterministic Kernel authorization reference passed.")
print("STATUS: KERNEL P0 TRUST BOUNDARY READY")
