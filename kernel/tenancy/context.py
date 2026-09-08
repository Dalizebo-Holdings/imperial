from __future__ import annotations

from dataclasses import dataclass

try:
    from identity_context import ACTOR_TYPES, IdentityContext
except ImportError:
    from ..identity.context import ACTOR_TYPES, IdentityContext


ENVIRONMENT_TYPES = {
    "DEVELOPMENT",
    "PREVIEW",
    "PRODUCTION",
}


class TenantContextError(ValueError):
    pass


@dataclass(frozen=True)
class TenantContext:
    organization_id: str
    workspace_id: str
    project_id: str
    environment_id: str
    environment_type: str
    actor_id: str
    actor_type: str
    correlation_id: str
    verified: bool
    verification_source: str

    def validate(self) -> None:
        required = {
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "environment_id": self.environment_id,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "correlation_id": self.correlation_id,
            "verification_source": self.verification_source,
        }

        missing = [
            key
            for key, value in required.items()
            if not str(value).strip()
        ]

        if missing:
            raise TenantContextError(
                "missing tenant context fields: "
                + ", ".join(missing)
            )

        actor_type = str(self.actor_type).strip().upper()
        if actor_type not in ACTOR_TYPES:
            raise TenantContextError(
                f"unsupported actor_type: {actor_type}"
            )

        env_type = str(self.environment_type).strip().upper()
        if env_type not in ENVIRONMENT_TYPES:
            raise TenantContextError(
                f"unsupported environment_type: {env_type}"
            )

        if not self.verified:
            raise TenantContextError(
                "tenant context must be verified"
            )

    def validate_identity(
        self,
        identity: IdentityContext,
    ) -> None:
        self.validate()
        identity.validate()

        if not identity.authenticated:
            raise TenantContextError(
                "identity is not authenticated"
            )

        if self.actor_id != identity.actor_id:
            raise TenantContextError(
                "tenant actor_id does not match identity"
            )

        if (
            str(self.actor_type).strip().upper()
            != str(identity.actor_type).strip().upper()
        ):
            raise TenantContextError(
                "tenant actor_type does not match identity"
            )

    def is_cross_tenant(
        self,
        target_organization_id: str | None,
    ) -> bool:
        if target_organization_id is None:
            return False

        target = str(target_organization_id).strip()
        if not target:
            raise TenantContextError(
                "target_organization_id must not be empty when provided"
            )

        return target != self.organization_id
