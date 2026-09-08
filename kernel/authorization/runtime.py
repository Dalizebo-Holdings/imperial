from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json

try:
    from identity_context import IdentityContext
    from tenant_context import TenantContext
except ImportError:
    from ..identity.context import IdentityContext
    from ..tenancy.context import TenantContext


POLICY_OUTCOMES = {
    "ALLOW",
    "DENY",
    "REQUIRE_APPROVAL",
    "REQUIRE_CONTEXT",
}


class AuthorizationError(ValueError):
    pass


@dataclass(frozen=True)
class PermissionDefinition:
    permission_id: str
    description: str
    sensitive: bool = False

    def validate(self) -> None:
        if not self.permission_id.strip():
            raise AuthorizationError(
                "permission_id must not be empty"
            )
        if "." not in self.permission_id:
            raise AuthorizationError(
                "permission_id must use resource.action form"
            )
        if not self.description.strip():
            raise AuthorizationError(
                "permission description must not be empty"
            )


@dataclass(frozen=True)
class RoleDefinition:
    role_id: str
    permissions: frozenset[str]
    organization_id: str
    workspace_id: str | None = None
    project_id: str | None = None
    environment_id: str | None = None

    def validate(self) -> None:
        if not self.role_id.strip():
            raise AuthorizationError(
                "role_id must not be empty"
            )
        if not self.organization_id.strip():
            raise AuthorizationError(
                "role organization_id must not be empty"
            )
        if not self.permissions:
            raise AuthorizationError(
                "role permissions must not be empty"
            )


class PermissionRegistry:
    def __init__(self) -> None:
        self._permissions: dict[str, PermissionDefinition] = {}

    def register(
        self,
        permission: PermissionDefinition,
    ) -> None:
        permission.validate()
        if permission.permission_id in self._permissions:
            raise AuthorizationError(
                f"permission already registered: {permission.permission_id}"
            )
        self._permissions[permission.permission_id] = permission

    def require(
        self,
        permission_id: str,
    ) -> PermissionDefinition:
        permission = self._permissions.get(permission_id)
        if permission is None:
            raise AuthorizationError(
                f"unknown permission: {permission_id}"
            )
        return permission


class RoleRegistry:
    def __init__(self) -> None:
        self._roles: dict[str, RoleDefinition] = {}

    def register(self, role: RoleDefinition) -> None:
        role.validate()
        if role.role_id in self._roles:
            raise AuthorizationError(
                f"role already registered: {role.role_id}"
            )
        self._roles[role.role_id] = role

    def get(self, role_id: str) -> RoleDefinition:
        role = self._roles.get(role_id)
        if role is None:
            raise AuthorizationError(
                f"unknown role: {role_id}"
            )
        return role


@dataclass(frozen=True)
class AuthorizationRequest:
    decision_request_id: str
    identity: IdentityContext
    tenant: TenantContext
    role_id: str
    required_permission: str
    resource_scope: str
    policy_outcome: str
    target_organization_id: str | None = None
    privileged: bool = False
    audit_behavior: str = "REQUIRED"

    def validate(self) -> None:
        if not self.decision_request_id.strip():
            raise AuthorizationError(
                "decision_request_id must not be empty"
            )

        self.identity.validate()
        self.tenant.validate_identity(self.identity)

        for name, value in {
            "role_id": self.role_id,
            "required_permission": self.required_permission,
            "resource_scope": self.resource_scope,
            "audit_behavior": self.audit_behavior,
        }.items():
            if not str(value).strip():
                raise AuthorizationError(
                    f"{name} must not be empty"
                )

        policy = self.policy_outcome.strip().upper()
        if policy not in POLICY_OUTCOMES:
            raise AuthorizationError(
                f"invalid policy outcome: {policy}"
            )


@dataclass(frozen=True)
class KernelAuthorizationDecision:
    authorized: bool
    outcome: str
    authorization_ref: str
    reason: str
    audit_event: dict


def _digest(payload: dict) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _role_matches_tenant(
    role: RoleDefinition,
    tenant: TenantContext,
) -> bool:
    if role.organization_id != tenant.organization_id:
        return False
    if (
        role.workspace_id is not None
        and role.workspace_id != tenant.workspace_id
    ):
        return False
    if (
        role.project_id is not None
        and role.project_id != tenant.project_id
    ):
        return False
    if (
        role.environment_id is not None
        and role.environment_id != tenant.environment_id
    ):
        return False
    return True


def authorize(
    *,
    request: AuthorizationRequest,
    permissions: PermissionRegistry,
    roles: RoleRegistry,
) -> KernelAuthorizationDecision:
    try:
        request.validate()
        permission = permissions.require(
            request.required_permission
        )
        role = roles.get(request.role_id)
    except (AuthorizationError, ValueError) as exc:
        material = {
            "decision_request_id": request.decision_request_id,
            "correlation_id": request.tenant.correlation_id,
            "required_permission": request.required_permission,
            "result": "DENY",
            "reason": "invalid_authorization_context",
        }
        ref = "kernel_auth_" + _digest(material)[:24]
        return KernelAuthorizationDecision(
            authorized=False,
            outcome="DENY",
            authorization_ref=ref,
            reason="invalid_authorization_context",
            audit_event={
                "event_type": "kernel.authorization.denied",
                "authorization_ref": ref,
                **material,
            },
        )

    policy = request.policy_outcome.strip().upper()
    reason = "authorized"
    authorized = True

    if not request.identity.authenticated:
        authorized = False
        reason = "identity_not_authenticated"
    elif policy != "ALLOW":
        authorized = False
        reason = f"policy_{policy.lower()}"
    elif not _role_matches_tenant(role, request.tenant):
        authorized = False
        reason = "role_tenant_scope_mismatch"
    elif permission.permission_id not in role.permissions:
        authorized = False
        reason = "permission_not_granted"
    elif request.tenant.is_cross_tenant(
        request.target_organization_id
    ):
        if not request.privileged:
            authorized = False
            reason = "cross_tenant_requires_privileged_mode"
        elif "kernel.cross_tenant" not in role.permissions:
            authorized = False
            reason = "cross_tenant_permission_missing"

    outcome = "AUTHORIZED" if authorized else "DENY"

    material = {
        "decision_request_id": request.decision_request_id,
        "actor_id": request.identity.actor_id,
        "actor_type": request.identity.actor_type,
        "organization_id": request.tenant.organization_id,
        "workspace_id": request.tenant.workspace_id,
        "project_id": request.tenant.project_id,
        "environment_id": request.tenant.environment_id,
        "correlation_id": request.tenant.correlation_id,
        "role_id": role.role_id,
        "required_permission": permission.permission_id,
        "resource_scope": request.resource_scope,
        "target_organization_id": request.target_organization_id,
        "privileged": request.privileged,
        "policy_outcome": policy,
        "outcome": outcome,
        "reason": reason,
    }

    ref = "kernel_auth_" + _digest(material)[:24]

    return KernelAuthorizationDecision(
        authorized=authorized,
        outcome=outcome,
        authorization_ref=ref,
        reason=reason,
        audit_event={
            "event_type": (
                "kernel.authorization.granted"
                if authorized
                else "kernel.authorization.denied"
            ),
            "authorization_ref": ref,
            **material,
            "audit_behavior": request.audit_behavior,
        },
    )
