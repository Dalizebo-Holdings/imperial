from __future__ import annotations

from dataclasses import dataclass, field, replace
import json
import re
from typing import Any

try:
    from .connector_model import AUTH_METHODS, SENSITIVE_FIELD_NAMES
except ImportError:
    from connector_model import AUTH_METHODS, SENSITIVE_FIELD_NAMES


class CredentialReferenceError(ValueError):
    pass


def _contains_sensitive_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).strip().lower() in SENSITIVE_FIELD_NAMES:
                return True
            if _contains_sensitive_key(item):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def _json_compatible(name: str, value: Any) -> None:
    try:
        json.dumps(value, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise CredentialReferenceError(
            f"{name} must be JSON-compatible"
        ) from exc


def _require_text(name: str, value: str) -> str:
    normalized = str(value).strip()

    if not normalized:
        raise CredentialReferenceError(
            f"{name} must not be empty"
        )

    return normalized


@dataclass
class CredentialDescriptor:
    credential_ref: str
    organization_id: str
    connector_id: str
    auth_method: str
    permission_scopes: list[str] = field(default_factory=list)
    owner: str = "Integrations Platform"
    version: str = "1"
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        self.credential_ref = _require_text(
            "credential_ref",
            self.credential_ref,
        )
        self.organization_id = _require_text(
            "organization_id",
            self.organization_id,
        )
        self.connector_id = _require_text(
            "connector_id",
            self.connector_id,
        )
        self.owner = _require_text("owner", self.owner)
        self.version = _require_text("version", self.version)

        if not re.fullmatch(
            r"(?:secret|credential)://[A-Za-z0-9._~:/-]+",
            self.credential_ref,
        ):
            raise CredentialReferenceError(
                "credential_ref must use secret:// or credential://"
            )

        self.auth_method = str(self.auth_method).strip().upper()

        if self.auth_method not in AUTH_METHODS - {"NONE"}:
            raise CredentialReferenceError(
                f"invalid credential auth method: {self.auth_method}"
            )

        scopes = [
            str(scope).strip()
            for scope in self.permission_scopes
            if str(scope).strip()
        ]

        if len(scopes) != len(set(scopes)):
            raise CredentialReferenceError(
                "permission_scopes contains duplicates"
            )

        self.permission_scopes = scopes

        _json_compatible("metadata", self.metadata)

        if _contains_sensitive_key(self.metadata):
            raise CredentialReferenceError(
                "credential metadata contains a raw sensitive field"
            )


@dataclass(frozen=True)
class CredentialContext:
    credential_ref: str
    organization_id: str
    connector_id: str
    auth_method: str
    approved_scopes: tuple[str, ...]
    descriptor_version: str


class CredentialReferenceAdapter:
    def __init__(self) -> None:
        self._descriptors: dict[str, CredentialDescriptor] = {}

    def register(
        self,
        descriptor: CredentialDescriptor,
        *,
        replace_existing: bool = False,
    ) -> None:
        descriptor.validate()

        if (
            descriptor.credential_ref in self._descriptors
            and not replace_existing
        ):
            raise CredentialReferenceError(
                f"credential reference already registered: {descriptor.credential_ref}"
            )

        self._descriptors[descriptor.credential_ref] = replace(
            descriptor
        )

    def disable(self, credential_ref: str) -> None:
        descriptor = self.get(credential_ref)
        descriptor.enabled = False
        self._descriptors[credential_ref] = descriptor

    def enable(self, credential_ref: str) -> None:
        descriptor = self.get(credential_ref)
        descriptor.enabled = True
        self._descriptors[credential_ref] = descriptor

    def get(
        self,
        credential_ref: str,
    ) -> CredentialDescriptor:
        ref = str(credential_ref).strip()
        descriptor = self._descriptors.get(ref)

        if descriptor is None:
            raise CredentialReferenceError(
                f"unknown credential reference: {ref}"
            )

        return replace(descriptor)

    def resolve_context(
        self,
        *,
        credential_ref: str,
        organization_id: str,
        connector_id: str,
        auth_method: str,
        requested_scopes: list[str] | None = None,
    ) -> CredentialContext:
        descriptor = self.get(credential_ref)
        descriptor.validate()

        if not descriptor.enabled:
            raise CredentialReferenceError(
                "credential reference is disabled"
            )

        if descriptor.organization_id != str(organization_id).strip():
            raise CredentialReferenceError(
                "credential organization scope mismatch"
            )

        if descriptor.connector_id != str(connector_id).strip():
            raise CredentialReferenceError(
                "credential connector binding mismatch"
            )

        normalized_auth = str(auth_method).strip().upper()

        if descriptor.auth_method != normalized_auth:
            raise CredentialReferenceError(
                "credential authentication method mismatch"
            )

        scopes = {
            str(scope).strip()
            for scope in (requested_scopes or [])
            if str(scope).strip()
        }

        undeclared = sorted(
            scopes - set(descriptor.permission_scopes)
        )

        if undeclared:
            raise CredentialReferenceError(
                "credential does not grant requested scopes: "
                + ", ".join(undeclared)
            )

        return CredentialContext(
            credential_ref=descriptor.credential_ref,
            organization_id=descriptor.organization_id,
            connector_id=descriptor.connector_id,
            auth_method=descriptor.auth_method,
            approved_scopes=tuple(sorted(scopes)),
            descriptor_version=descriptor.version,
        )

    def list_descriptors(self) -> list[CredentialDescriptor]:
        return [
            replace(descriptor)
            for descriptor in sorted(
                self._descriptors.values(),
                key=lambda item: item.credential_ref,
            )
        ]
