from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import re
from typing import Any


SECRET_STATES = {
    "ACTIVE",
    "DISABLED",
}

SECRET_REF_PATTERN = re.compile(
    r"(?:secret|vault|kms)://[A-Za-z0-9._~:/-]+"
)

ADAPTER_REF_PATTERN = re.compile(
    r"adapter://[A-Za-z0-9._~:/-]+"
)

PROVIDER_ID_PATTERN = re.compile(
    r"[a-z][a-z0-9._-]{1,63}"
)

SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
    "access_token",
    "refresh_token",
    "api_key",
    "password",
    "secret",
    "secret_value",
    "client_secret",
    "private_key",
    "session_token",
    "webhook_secret",
    "provider_credentials",
    "card_number",
    "cvv",
    "cvc",
    "pan",
}


class SecretsBaaSError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    result = str(value).strip()
    if not result:
        raise SecretsBaaSError(
            f"{name} must not be empty"
        )
    return result


def _time(
    value: str | None = None,
) -> datetime:
    if value is None:
        return datetime.now(
            timezone.utc
        )

    try:
        parsed = datetime.fromisoformat(
            value
        )
    except ValueError as exc:
        raise SecretsBaaSError(
            "timestamp must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise SecretsBaaSError(
            "timestamp must be timezone-aware"
        )

    return parsed


def _contains_sensitive(
    value: Any,
) -> bool:
    if isinstance(
        value,
        dict,
    ):
        for key, item in value.items():
            if (
                str(key).strip().lower()
                in SENSITIVE_KEYS
            ):
                return True

            if _contains_sensitive(
                item
            ):
                return True

    elif isinstance(
        value,
        (list, tuple),
    ):
        return any(
            _contains_sensitive(item)
            for item in value
        )

    return False


def _validate_metadata(
    value: dict[str, Any],
) -> None:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise SecretsBaaSError(
            "secret metadata must be JSON-compatible"
        ) from exc

    if len(encoded) > 8192:
        raise SecretsBaaSError(
            "secret metadata exceeds 8192 bytes"
        )

    if _contains_sensitive(
        value
    ):
        raise SecretsBaaSError(
            "secret metadata contains secret-bearing fields"
        )


@dataclass(frozen=True)
class TenantScope:
    organization_id: str
    workspace_id: str
    project_id: str
    environment_id: str

    def validate(self) -> None:
        for name, value in {
            "organization_id": (
                self.organization_id
            ),
            "workspace_id": (
                self.workspace_id
            ),
            "project_id": (
                self.project_id
            ),
            "environment_id": (
                self.environment_id
            ),
        }.items():
            _text(
                name,
                value,
            )


@dataclass(frozen=True)
class SecretProvider:
    provider_id: str
    adapter_ref: str
    control_credential_ref: str
    encryption_at_rest_required: bool
    supports_rotation: bool
    enabled: bool = True

    def validate(self) -> None:
        if not PROVIDER_ID_PATTERN.fullmatch(
            str(
                self.provider_id
            ).strip()
        ):
            raise SecretsBaaSError(
                "provider_id must be a safe identifier"
            )

        if not ADAPTER_REF_PATTERN.fullmatch(
            str(
                self.adapter_ref
            ).strip()
        ):
            raise SecretsBaaSError(
                "adapter_ref must use adapter://"
            )

        if not SECRET_REF_PATTERN.fullmatch(
            str(
                self.control_credential_ref
            ).strip()
        ):
            raise SecretsBaaSError(
                "control_credential_ref must be an opaque secret reference"
            )

        if not self.encryption_at_rest_required:
            raise SecretsBaaSError(
                "P0 secret providers must require encryption at rest"
            )


@dataclass(frozen=True)
class SecretRegistration:
    secret_id: str
    tenant: TenantScope
    name: str
    purpose: str
    owner: str
    provider_id: str
    secret_ref: str
    version: str
    allowed_consumers: tuple[
        str,
        ...
    ]
    rotation_interval_days: int | None
    rotated_at: str
    state: str
    metadata: dict[str, Any]

    def validate(self) -> None:
        for name, value in {
            "secret_id": (
                self.secret_id
            ),
            "name": self.name,
            "purpose": (
                self.purpose
            ),
            "owner": self.owner,
            "version": (
                self.version
            ),
        }.items():
            _text(
                name,
                value,
            )

        self.tenant.validate()

        if not PROVIDER_ID_PATTERN.fullmatch(
            str(
                self.provider_id
            ).strip()
        ):
            raise SecretsBaaSError(
                "provider_id must be a safe identifier"
            )

        if not SECRET_REF_PATTERN.fullmatch(
            str(
                self.secret_ref
            ).strip()
        ):
            raise SecretsBaaSError(
                "secret_ref must use secret://, vault://, or kms://"
            )

        consumers = tuple(
            str(
                value
            ).strip()
            for value in self.allowed_consumers
            if str(
                value
            ).strip()
        )

        if not consumers:
            raise SecretsBaaSError(
                "allowed_consumers must not be empty"
            )

        if len(
            consumers
        ) != len(
            set(
                consumers
            )
        ):
            raise SecretsBaaSError(
                "allowed_consumers contains duplicates"
            )

        if (
            self.rotation_interval_days
            is not None
        ):
            if (
                not isinstance(
                    self.rotation_interval_days,
                    int,
                )
                or self.rotation_interval_days < 1
                or self.rotation_interval_days > 3650
            ):
                raise SecretsBaaSError(
                    "rotation_interval_days must be 1..3650"
                )

        _time(
            self.rotated_at
        )

        if self.state not in SECRET_STATES:
            raise SecretsBaaSError(
                f"invalid secret state: {self.state}"
            )

        _validate_metadata(
            self.metadata
        )


@dataclass(frozen=True)
class SecretAccessPlan:
    secret_id: str
    secret_ref: str
    provider_id: str
    provider_adapter_ref: str
    purpose: str
    consumer: str
    descriptor_version: str
    tenant_context: dict[
        str,
        str,
    ]
    correlation_id: str
    kernel_authorization_ref: str
    audit_event: dict[
        str,
        Any,
    ]
    state: str = (
        "READY_FOR_SECRET_MANAGER_ADAPTER"
    )


@dataclass(frozen=True)
class SecretRotationPlan:
    rotation_id: str
    secret_id: str
    current_secret_ref: str
    provider_id: str
    provider_adapter_ref: str
    provider_control_credential_ref: str
    current_version: str
    next_version: str
    tenant_context: dict[
        str,
        str,
    ]
    correlation_id: str
    kernel_authorization_ref: str
    audit_event: dict[
        str,
        Any,
    ]
    state: str = (
        "READY_FOR_SECRET_MANAGER_ROTATION_ADAPTER"
    )


class SecretsService:
    def __init__(
        self,
        *,
        kernel_registry: Any,
        kernel_descriptor_type: Any,
    ) -> None:
        if kernel_registry is None:
            raise SecretsBaaSError(
                "kernel_registry is required"
            )

        if not callable(
            kernel_descriptor_type
        ):
            raise SecretsBaaSError(
                "kernel_descriptor_type must be callable"
            )

        self._kernel_registry = (
            kernel_registry
        )
        self._kernel_descriptor_type = (
            kernel_descriptor_type
        )
        self._providers: dict[
            str,
            SecretProvider,
        ] = {}
        self._secrets: dict[
            str,
            SecretRegistration,
        ] = {}
        self._ref_to_secret_id: dict[
            str,
            str,
        ] = {}

    @staticmethod
    def _validate_request_context(
        request_context: Any,
    ) -> None:
        if hasattr(
            request_context,
            "validate",
        ):
            request_context.validate()

        for name in [
            "request_id",
            "correlation_id",
            "service",
            "operation",
            "organization_id",
            "workspace_id",
            "project_id",
            "environment_id",
            "actor_id",
            "actor_type",
            "kernel_authorization_ref",
        ]:
            _text(
                name,
                getattr(
                    request_context,
                    name,
                    None,
                ),
            )

        if (
            str(
                request_context.service
            ).strip()
            != "secrets"
        ):
            raise SecretsBaaSError(
                "SecretsService requires service=secrets"
            )

        if not str(
            request_context.kernel_authorization_ref
        ).startswith(
            "kernel_auth_"
        ):
            raise SecretsBaaSError(
                "secret operations require Kernel authorization evidence"
            )

    @staticmethod
    def _tenant_from_context(
        request_context: Any,
    ) -> TenantScope:
        tenant = TenantScope(
            organization_id=(
                request_context.organization_id
            ),
            workspace_id=(
                request_context.workspace_id
            ),
            project_id=(
                request_context.project_id
            ),
            environment_id=(
                request_context.environment_id
            ),
        )
        tenant.validate()
        return tenant

    @staticmethod
    def _same_tenant(
        left: TenantScope,
        right: TenantScope,
    ) -> bool:
        return (
            left.organization_id
            == right.organization_id
            and left.workspace_id
            == right.workspace_id
            and left.project_id
            == right.project_id
            and left.environment_id
            == right.environment_id
        )

    def register_provider(
        self,
        *,
        provider: SecretProvider,
        request_context: Any,
    ) -> None:
        self._validate_request_context(
            request_context
        )
        provider.validate()

        if (
            provider.provider_id
            in self._providers
        ):
            raise SecretsBaaSError(
                "secret provider already registered"
            )

        self._providers[
            provider.provider_id
        ] = provider

    def register_secret(
        self,
        *,
        registration: SecretRegistration,
        request_context: Any,
    ) -> dict[
        str,
        Any,
    ]:
        self._validate_request_context(
            request_context
        )
        registration.validate()

        tenant = self._tenant_from_context(
            request_context
        )

        if not self._same_tenant(
            registration.tenant,
            tenant,
        ):
            raise SecretsBaaSError(
                "secret tenant scope mismatch"
            )

        provider = self._require_provider(
            registration.provider_id
        )

        if (
            registration.secret_id
            in self._secrets
        ):
            raise SecretsBaaSError(
                "secret_id already registered"
            )

        if (
            registration.secret_ref
            in self._ref_to_secret_id
        ):
            raise SecretsBaaSError(
                "secret_ref already registered"
            )

        descriptor = (
            self._kernel_descriptor_type(
                secret_ref=(
                    registration.secret_ref
                ),
                organization_id=(
                    registration.tenant.organization_id
                ),
                purpose=(
                    registration.purpose
                ),
                owner=(
                    registration.owner
                ),
                version=(
                    registration.version
                ),
                environment_id=(
                    registration.tenant.environment_id
                ),
                allowed_consumers=list(
                    registration.allowed_consumers
                ),
                rotation_required=(
                    registration.rotation_interval_days
                    is not None
                ),
                enabled=(
                    registration.state
                    == "ACTIVE"
                ),
                metadata=dict(
                    registration.metadata
                ),
            )
        )

        self._kernel_registry.register(
            descriptor
        )

        self._secrets[
            registration.secret_id
        ] = registration
        self._ref_to_secret_id[
            registration.secret_ref
        ] = registration.secret_id

        return {
            "registration": (
                registration
            ),
            "provider_policy": {
                "provider_id": (
                    provider.provider_id
                ),
                "encryption_at_rest_required": (
                    provider.encryption_at_rest_required
                ),
            },
            "audit_event": (
                self._audit_event(
                    action=(
                        "secrets.register"
                    ),
                    registration=(
                        registration
                    ),
                    request_context=(
                        request_context
                    ),
                    timestamp=(
                        registration.rotated_at
                    ),
                    metadata={
                        "provider_id": (
                            provider.provider_id
                        ),
                        "version": (
                            registration.version
                        ),
                    },
                )
            ),
        }

    def access_plan(
        self,
        *,
        secret_id: str,
        consumer: str,
        request_context: Any,
        accessed_at: str | None = None,
    ) -> SecretAccessPlan:
        registration = (
            self._get_secret(
                secret_id=secret_id,
                request_context=(
                    request_context
                ),
            )
        )

        if (
            registration.state
            != "ACTIVE"
        ):
            raise SecretsBaaSError(
                "secret is disabled"
            )

        consumer_name = _text(
            "consumer",
            consumer,
        )

        context = (
            self._kernel_registry.resolve(
                secret_ref=(
                    registration.secret_ref
                ),
                organization_id=(
                    registration.tenant.organization_id
                ),
                environment_id=(
                    registration.tenant.environment_id
                ),
                consumer=(
                    consumer_name
                ),
            )
        )

        provider = self._require_provider(
            registration.provider_id
        )

        now = _time(
            accessed_at
        ).isoformat()

        return SecretAccessPlan(
            secret_id=(
                registration.secret_id
            ),
            secret_ref=(
                context.secret_ref
            ),
            provider_id=(
                provider.provider_id
            ),
            provider_adapter_ref=(
                provider.adapter_ref
            ),
            purpose=(
                context.purpose
            ),
            consumer=(
                context.consumer
            ),
            descriptor_version=(
                context.descriptor_version
            ),
            tenant_context={
                "organization_id": (
                    registration.tenant.organization_id
                ),
                "workspace_id": (
                    registration.tenant.workspace_id
                ),
                "project_id": (
                    registration.tenant.project_id
                ),
                "environment_id": (
                    registration.tenant.environment_id
                ),
            },
            correlation_id=(
                request_context.correlation_id
            ),
            kernel_authorization_ref=(
                request_context.kernel_authorization_ref
            ),
            audit_event=(
                self._audit_event(
                    action=(
                        "secrets.access"
                    ),
                    registration=(
                        registration
                    ),
                    request_context=(
                        request_context
                    ),
                    timestamp=now,
                    metadata={
                        "consumer": (
                            consumer_name
                        ),
                        "version": (
                            context.descriptor_version
                        ),
                    },
                )
            ),
        )

    def rotation_due(
        self,
        *,
        secret_id: str,
        request_context: Any,
        now: str | None = None,
    ) -> bool:
        registration = (
            self._get_secret(
                secret_id=secret_id,
                request_context=(
                    request_context
                ),
            )
        )

        if (
            registration.rotation_interval_days
            is None
        ):
            return False

        current = _time(
            now
        )

        due_at = (
            _time(
                registration.rotated_at
            )
            + timedelta(
                days=(
                    registration.rotation_interval_days
                )
            )
        )

        return current >= due_at

    def plan_rotation(
        self,
        *,
        secret_id: str,
        next_version: str,
        request_context: Any,
        planned_at: str | None = None,
    ) -> SecretRotationPlan:
        registration = (
            self._get_secret(
                secret_id=secret_id,
                request_context=(
                    request_context
                ),
            )
        )

        if (
            registration.state
            != "ACTIVE"
        ):
            raise SecretsBaaSError(
                "disabled secret cannot rotate"
            )

        provider = self._require_provider(
            registration.provider_id
        )

        if not provider.supports_rotation:
            raise SecretsBaaSError(
                "secret provider does not support rotation"
            )

        version = _text(
            "next_version",
            next_version,
        )

        if (
            version
            == registration.version
        ):
            raise SecretsBaaSError(
                "rotation requires a new version"
            )

        material = {
            "secret_id": (
                registration.secret_id
            ),
            "current_secret_ref": (
                registration.secret_ref
            ),
            "current_version": (
                registration.version
            ),
            "next_version": version,
            "organization_id": (
                registration.tenant.organization_id
            ),
            "environment_id": (
                registration.tenant.environment_id
            ),
        }

        rotation_id = (
            "secret_rotation_"
            + sha256(
                json.dumps(
                    material,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()[:24]
        )

        now = _time(
            planned_at
        ).isoformat()

        return SecretRotationPlan(
            rotation_id=rotation_id,
            secret_id=(
                registration.secret_id
            ),
            current_secret_ref=(
                registration.secret_ref
            ),
            provider_id=(
                provider.provider_id
            ),
            provider_adapter_ref=(
                provider.adapter_ref
            ),
            provider_control_credential_ref=(
                provider.control_credential_ref
            ),
            current_version=(
                registration.version
            ),
            next_version=version,
            tenant_context={
                "organization_id": (
                    registration.tenant.organization_id
                ),
                "workspace_id": (
                    registration.tenant.workspace_id
                ),
                "project_id": (
                    registration.tenant.project_id
                ),
                "environment_id": (
                    registration.tenant.environment_id
                ),
            },
            correlation_id=(
                request_context.correlation_id
            ),
            kernel_authorization_ref=(
                request_context.kernel_authorization_ref
            ),
            audit_event=(
                self._audit_event(
                    action=(
                        "secrets.rotation.plan"
                    ),
                    registration=(
                        registration
                    ),
                    request_context=(
                        request_context
                    ),
                    timestamp=now,
                    metadata={
                        "rotation_id": (
                            rotation_id
                        ),
                        "current_version": (
                            registration.version
                        ),
                        "next_version": (
                            version
                        ),
                    },
                )
            ),
        )

    def confirm_rotation(
        self,
        *,
        rotation_plan: SecretRotationPlan,
        new_secret_ref: str,
        rotated_at: str,
        request_context: Any,
    ) -> dict[
        str,
        Any,
    ]:
        registration = (
            self._get_secret(
                secret_id=(
                    rotation_plan.secret_id
                ),
                request_context=(
                    request_context
                ),
            )
        )

        if (
            rotation_plan.state
            != "READY_FOR_SECRET_MANAGER_ROTATION_ADAPTER"
        ):
            raise SecretsBaaSError(
                "invalid rotation plan state"
            )

        if (
            rotation_plan.current_secret_ref
            != registration.secret_ref
            or rotation_plan.current_version
            != registration.version
        ):
            raise SecretsBaaSError(
                "rotation plan is stale"
            )

        new_ref = str(
            new_secret_ref
        ).strip()

        if not SECRET_REF_PATTERN.fullmatch(
            new_ref
        ):
            raise SecretsBaaSError(
                "new_secret_ref must be an opaque secret reference"
            )

        if (
            new_ref
            == registration.secret_ref
        ):
            raise SecretsBaaSError(
                "rotation requires a new secret reference"
            )

        if (
            new_ref
            in self._ref_to_secret_id
        ):
            raise SecretsBaaSError(
                "new secret reference already registered"
            )

        timestamp = _time(
            rotated_at
        ).isoformat()

        descriptor = (
            self._kernel_descriptor_type(
                secret_ref=(
                    new_ref
                ),
                organization_id=(
                    registration.tenant.organization_id
                ),
                purpose=(
                    registration.purpose
                ),
                owner=(
                    registration.owner
                ),
                version=(
                    rotation_plan.next_version
                ),
                environment_id=(
                    registration.tenant.environment_id
                ),
                allowed_consumers=list(
                    registration.allowed_consumers
                ),
                rotation_required=(
                    registration.rotation_interval_days
                    is not None
                ),
                enabled=True,
                metadata=dict(
                    registration.metadata
                ),
            )
        )

        self._kernel_registry.register(
            descriptor
        )
        self._kernel_registry.disable(
            registration.secret_ref
        )

        old_ref = (
            registration.secret_ref
        )

        updated = replace(
            registration,
            secret_ref=new_ref,
            version=(
                rotation_plan.next_version
            ),
            rotated_at=timestamp,
        )
        updated.validate()

        self._secrets[
            registration.secret_id
        ] = updated
        self._ref_to_secret_id[
            new_ref
        ] = updated.secret_id

        return {
            "registration": (
                updated
            ),
            "old_secret_ref": (
                old_ref
            ),
            "audit_event": (
                self._audit_event(
                    action=(
                        "secrets.rotation.confirm"
                    ),
                    registration=(
                        updated
                    ),
                    request_context=(
                        request_context
                    ),
                    timestamp=timestamp,
                    metadata={
                        "rotation_id": (
                            rotation_plan.rotation_id
                        ),
                        "old_secret_ref": (
                            old_ref
                        ),
                        "new_version": (
                            updated.version
                        ),
                    },
                )
            ),
        }

    def disable(
        self,
        *,
        secret_id: str,
        request_context: Any,
        disabled_at: str | None = None,
    ) -> dict[
        str,
        Any,
    ]:
        registration = (
            self._get_secret(
                secret_id=secret_id,
                request_context=(
                    request_context
                ),
            )
        )

        if (
            registration.state
            == "DISABLED"
        ):
            raise SecretsBaaSError(
                "secret is already disabled"
            )

        self._kernel_registry.disable(
            registration.secret_ref
        )

        updated = replace(
            registration,
            state="DISABLED",
        )

        self._secrets[
            secret_id
        ] = updated

        now = _time(
            disabled_at
        ).isoformat()

        return {
            "registration": (
                updated
            ),
            "audit_event": (
                self._audit_event(
                    action=(
                        "secrets.disable"
                    ),
                    registration=(
                        updated
                    ),
                    request_context=(
                        request_context
                    ),
                    timestamp=now,
                    metadata={
                        "version": (
                            updated.version
                        ),
                    },
                )
            ),
        }

    def _get_secret(
        self,
        *,
        secret_id: str,
        request_context: Any,
    ) -> SecretRegistration:
        self._validate_request_context(
            request_context
        )

        registration = (
            self._secrets.get(
                str(
                    secret_id
                ).strip()
            )
        )

        if registration is None:
            raise SecretsBaaSError(
                "secret registration not found"
            )

        tenant = self._tenant_from_context(
            request_context
        )

        if not self._same_tenant(
            registration.tenant,
            tenant,
        ):
            raise SecretsBaaSError(
                "cross-tenant secret access denied"
            )

        return registration

    def _require_provider(
        self,
        provider_id: str,
    ) -> SecretProvider:
        provider = self._providers.get(
            str(
                provider_id
            ).strip()
        )

        if provider is None:
            raise SecretsBaaSError(
                "secret provider not found"
            )

        if not provider.enabled:
            raise SecretsBaaSError(
                "secret provider is disabled"
            )

        return provider

    @staticmethod
    def _audit_event(
        *,
        action: str,
        registration: SecretRegistration,
        request_context: Any,
        timestamp: str,
        metadata: dict[str, Any],
    ) -> dict[
        str,
        Any,
    ]:
        material = {
            "action": action,
            "secret_id": (
                registration.secret_id
            ),
            "secret_ref": (
                registration.secret_ref
            ),
            "correlation_id": (
                request_context.correlation_id
            ),
            "timestamp": timestamp,
        }

        audit_id = (
            "audit_secret_"
            + sha256(
                json.dumps(
                    material,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()[:24]
        )

        return {
            "audit_id": audit_id,
            "organization_id": (
                registration.tenant.organization_id
            ),
            "actor_type": (
                request_context.actor_type
            ),
            "actor_id": (
                request_context.actor_id
            ),
            "action": action,
            "resource_type": (
                "secret_reference"
            ),
            "resource_id": (
                registration.secret_id
            ),
            "timestamp": timestamp,
            "correlation_id": (
                request_context.correlation_id
            ),
            "metadata": {
                "secret_ref": (
                    registration.secret_ref
                ),
                **metadata,
            },
        }
