from __future__ import annotations

from dataclasses import dataclass, field, replace
import json
import re
from typing import Any


SENSITIVE_KEYS = {
    "authorization",
    "access_token",
    "refresh_token",
    "api_key",
    "password",
    "secret",
    "secret_value",
    "client_secret",
    "private_key",
    "cookie",
    "session_token",
    "webhook_secret",
}


class SecretReferenceError(ValueError):
    pass


def _contains_sensitive_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).strip().lower() in SENSITIVE_KEYS:
                return True
            if _contains_sensitive_key(item):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_sensitive_key(item) for item in value)
    return False


@dataclass
class SecretDescriptor:
    secret_ref: str
    organization_id: str
    purpose: str
    owner: str
    version: str
    environment_id: str
    allowed_consumers: list[str]
    rotation_required: bool = True
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        required = {
            "secret_ref": self.secret_ref,
            "organization_id": self.organization_id,
            "purpose": self.purpose,
            "owner": self.owner,
            "version": self.version,
            "environment_id": self.environment_id,
        }

        missing = [
            name
            for name, value in required.items()
            if not str(value).strip()
        ]

        if missing:
            raise SecretReferenceError(
                "missing secret descriptor fields: "
                + ", ".join(missing)
            )

        if not re.fullmatch(
            r"(?:secret|vault|kms)://[A-Za-z0-9._~:/-]+",
            self.secret_ref,
        ):
            raise SecretReferenceError(
                "secret_ref must use secret://, vault://, or kms://"
            )

        consumers = [
            str(value).strip()
            for value in self.allowed_consumers
            if str(value).strip()
        ]

        if not consumers:
            raise SecretReferenceError(
                "allowed_consumers must not be empty"
            )

        if len(consumers) != len(set(consumers)):
            raise SecretReferenceError(
                "allowed_consumers contains duplicates"
            )

        self.allowed_consumers = consumers

        try:
            json.dumps(
                self.metadata,
                sort_keys=True,
                separators=(",", ":"),
            )
        except (TypeError, ValueError) as exc:
            raise SecretReferenceError(
                "secret metadata must be JSON-compatible"
            ) from exc

        if _contains_sensitive_key(self.metadata):
            raise SecretReferenceError(
                "secret descriptor metadata contains raw secret material"
            )


@dataclass(frozen=True)
class SecretContext:
    secret_ref: str
    organization_id: str
    environment_id: str
    purpose: str
    consumer: str
    descriptor_version: str


class SecretReferenceRegistry:
    def __init__(self) -> None:
        self._descriptors: dict[str, SecretDescriptor] = {}

    def register(
        self,
        descriptor: SecretDescriptor,
        *,
        replace_existing: bool = False,
    ) -> None:
        descriptor.validate()

        if (
            descriptor.secret_ref in self._descriptors
            and not replace_existing
        ):
            raise SecretReferenceError(
                f"secret reference already registered: {descriptor.secret_ref}"
            )

        self._descriptors[descriptor.secret_ref] = replace(
            descriptor
        )

    def get(self, secret_ref: str) -> SecretDescriptor:
        ref = str(secret_ref).strip()
        descriptor = self._descriptors.get(ref)

        if descriptor is None:
            raise SecretReferenceError(
                f"unknown secret reference: {ref}"
            )

        return replace(descriptor)

    def disable(self, secret_ref: str) -> None:
        descriptor = self.get(secret_ref)
        descriptor.enabled = False
        self._descriptors[secret_ref] = descriptor

    def resolve(
        self,
        *,
        secret_ref: str,
        organization_id: str,
        environment_id: str,
        consumer: str,
    ) -> SecretContext:
        descriptor = self.get(secret_ref)
        descriptor.validate()

        if not descriptor.enabled:
            raise SecretReferenceError(
                "secret reference is disabled"
            )

        if descriptor.organization_id != str(
            organization_id
        ).strip():
            raise SecretReferenceError(
                "secret organization scope mismatch"
            )

        if descriptor.environment_id != str(
            environment_id
        ).strip():
            raise SecretReferenceError(
                "secret environment scope mismatch"
            )

        consumer_name = str(consumer).strip()

        if consumer_name not in descriptor.allowed_consumers:
            raise SecretReferenceError(
                "consumer is not authorized for secret reference"
            )

        return SecretContext(
            secret_ref=descriptor.secret_ref,
            organization_id=descriptor.organization_id,
            environment_id=descriptor.environment_id,
            purpose=descriptor.purpose,
            consumer=consumer_name,
            descriptor_version=descriptor.version,
        )
