from __future__ import annotations

from dataclasses import dataclass


P0_SERVICES = {
    "authentication",
    "database",
    "storage",
    "functions",
    "api_gateway",
    "events",
    "webhooks",
    "background_jobs",
    "audit",
    "logging",
    "usage_metering",
    "subscription_billing",
    "payments",
    "currency_conversion",
    "secrets",
    "backups",
}


class BaaSRequestError(ValueError):
    pass


@dataclass(frozen=True)
class BaaSRequestContext:
    request_id: str
    correlation_id: str
    service: str
    operation: str
    organization_id: str
    workspace_id: str
    project_id: str
    environment_id: str
    actor_id: str
    actor_type: str
    kernel_authorization_ref: str
    idempotency_key: str

    def validate(self) -> None:
        required = {
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "service": self.service,
            "operation": self.operation,
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "environment_id": self.environment_id,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "kernel_authorization_ref": self.kernel_authorization_ref,
            "idempotency_key": self.idempotency_key,
        }

        missing = [
            name
            for name, value in required.items()
            if not str(value).strip()
        ]

        if missing:
            raise BaaSRequestError(
                "missing BaaS request fields: "
                + ", ".join(missing)
            )

        service = str(self.service).strip()

        if service not in P0_SERVICES:
            raise BaaSRequestError(
                f"unknown BaaS P0 service: {service}"
            )

        if not str(
            self.kernel_authorization_ref
        ).startswith("kernel_auth_"):
            raise BaaSRequestError(
                "kernel_authorization_ref is invalid"
            )
