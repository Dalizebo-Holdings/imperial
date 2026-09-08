from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from typing import Any

try:
    from .connector_model import (
        AUTH_METHODS,
        CIRCUIT_STATES,
        ConnectorDefinition,
        SENSITIVE_FIELD_NAMES,
    )
    from .connector_registry import ConnectorRegistry
except ImportError:
    from connector_model import (
        AUTH_METHODS,
        CIRCUIT_STATES,
        ConnectorDefinition,
        SENSITIVE_FIELD_NAMES,
    )
    from connector_registry import ConnectorRegistry


ALLOWED_RESPONSE_STATUS = {
    "SUCCESS",
    "ERROR",
    "RATE_LIMITED",
    "AUTHORIZATION_REQUIRED",
    "CIRCUIT_OPEN",
    "SAFE_FAILURE",
}


class RuntimeContractError(ValueError):
    pass


def _json_compatible(name: str, value: Any) -> None:
    try:
        json.dumps(value, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise RuntimeContractError(
            f"{name} must be JSON-compatible"
        ) from exc


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


@dataclass(frozen=True)
class IntegrationAuthorization:
    pillars_approved: bool
    kernel_authorized: bool
    authorization_ref: str

    def validate(self) -> None:
        if not self.authorization_ref.strip():
            raise RuntimeContractError(
                "authorization_ref must not be empty"
            )


@dataclass
class ConnectorRequest:
    request_id: str
    connector_id: str
    connector_version: str
    operation: str
    organization_id: str
    correlation_id: str
    idempotency_key: str
    auth_method: str
    credential_ref: str
    payload: Any
    permission_scopes: list[str] = field(default_factory=list)
    timeout_seconds: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate_basic(self) -> None:
        required = {
            "request_id": self.request_id,
            "connector_id": self.connector_id,
            "connector_version": self.connector_version,
            "operation": self.operation,
            "organization_id": self.organization_id,
            "correlation_id": self.correlation_id,
            "idempotency_key": self.idempotency_key,
            "auth_method": self.auth_method,
        }

        missing = [
            key
            for key, value in required.items()
            if not str(value).strip()
        ]

        if missing:
            raise RuntimeContractError(
                "missing connector request fields: " + ", ".join(missing)
            )

        self.auth_method = self.auth_method.strip().upper()

        if self.auth_method not in AUTH_METHODS:
            raise RuntimeContractError(
                f"unsupported auth method: {self.auth_method}"
            )

        _json_compatible("payload", self.payload)
        _json_compatible("metadata", self.metadata)

        if _contains_sensitive_key(self.payload):
            raise RuntimeContractError(
                "payload contains a raw sensitive field"
            )

        if _contains_sensitive_key(self.metadata):
            raise RuntimeContractError(
                "metadata contains a raw sensitive field"
            )


@dataclass
class CircuitState:
    state: str = "CLOSED"
    failure_count: int = 0

    def validate(self) -> None:
        self.state = self.state.strip().upper()

        if self.state not in CIRCUIT_STATES:
            raise RuntimeContractError(
                f"invalid circuit state: {self.state}"
            )

        if self.failure_count < 0:
            raise RuntimeContractError(
                "failure_count must be >= 0"
            )


@dataclass
class PreparedConnectorCall:
    request: ConnectorRequest
    connector: ConnectorDefinition
    authorization_ref: str
    effective_timeout_seconds: int
    state: str = "READY_FOR_ADAPTER_EXECUTION"

    def to_dict(self) -> dict:
        return {
            "request": asdict(self.request),
            "connector": self.connector.to_dict(),
            "authorization_ref": self.authorization_ref,
            "effective_timeout_seconds": self.effective_timeout_seconds,
            "state": self.state,
        }


def prepare_call(
    *,
    registry: ConnectorRegistry,
    request: ConnectorRequest,
    authorization: IntegrationAuthorization,
    circuit_state: CircuitState | None = None,
) -> PreparedConnectorCall:
    request.validate_basic()
    authorization.validate()

    if not (
        authorization.pillars_approved
        and authorization.kernel_authorized
    ):
        raise RuntimeContractError(
            "connector execution requires Pillars OS and Kernel authorization"
        )

    connector = registry.resolve_compatible(
        request.connector_id,
        request.connector_version,
    )
    connector.validate()

    if not connector.enabled:
        raise RuntimeContractError(
            f"connector is disabled: {connector.connector_id}@{connector.version}"
        )

    if request.operation not in connector.supported_operations:
        raise RuntimeContractError(
            f"unsupported operation: {request.operation}"
        )

    if request.auth_method not in connector.supported_auth_methods:
        raise RuntimeContractError(
            f"auth method not supported by connector: {request.auth_method}"
        )

    if (
        connector.credential_reference_required
        and request.auth_method != "NONE"
        and not str(request.credential_ref).strip()
    ):
        raise RuntimeContractError(
            "credential_ref is required"
        )

    if request.auth_method == "NONE" and request.credential_ref:
        raise RuntimeContractError(
            "credential_ref must be empty for NONE auth"
        )

    undeclared_scopes = sorted(
        set(request.permission_scopes)
        - set(connector.permission_scopes)
    )

    if undeclared_scopes:
        raise RuntimeContractError(
            "undeclared permission scopes: "
            + ", ".join(undeclared_scopes)
        )

    timeout = (
        connector.timeout_seconds
        if request.timeout_seconds is None
        else request.timeout_seconds
    )

    if not isinstance(timeout, int) or timeout < 1:
        raise RuntimeContractError(
            "timeout_seconds must be a positive integer"
        )

    if timeout > connector.timeout_seconds:
        raise RuntimeContractError(
            "requested timeout exceeds connector maximum"
        )

    circuit = circuit_state or CircuitState()
    circuit.validate()

    if circuit.state == "OPEN":
        raise RuntimeContractError(
            "connector circuit is OPEN"
        )

    return PreparedConnectorCall(
        request=request,
        connector=connector,
        authorization_ref=authorization.authorization_ref,
        effective_timeout_seconds=timeout,
    )


@dataclass
class NormalizedConnectorError:
    code: str
    message: str
    provider_code: str | None = None
    retryable: bool = False
    category: str = "PROVIDER"

    def validate(self) -> None:
        if not self.code.strip():
            raise RuntimeContractError(
                "error code must not be empty"
            )
        if not self.message.strip():
            raise RuntimeContractError(
                "error message must not be empty"
            )
        if _contains_sensitive_key(
            {"message": self.message}
        ):
            raise RuntimeContractError(
                "error message contains sensitive material"
            )


@dataclass
class ConnectorResponse:
    request_id: str
    connector_id: str
    correlation_id: str
    status: str
    provider_status: str | None = None
    data: Any = None
    error: NormalizedConnectorError | None = None
    retryable: bool = False
    rate_limit: dict[str, Any] = field(default_factory=dict)
    audit_event: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        self.status = self.status.strip().upper()

        if self.status not in ALLOWED_RESPONSE_STATUS:
            raise RuntimeContractError(
                f"invalid response status: {self.status}"
            )

        for name, value in {
            "request_id": self.request_id,
            "connector_id": self.connector_id,
            "correlation_id": self.correlation_id,
        }.items():
            if not str(value).strip():
                raise RuntimeContractError(
                    f"{name} must not be empty"
                )

        _json_compatible("data", self.data)
        _json_compatible("rate_limit", self.rate_limit)
        _json_compatible("audit_event", self.audit_event)

        if _contains_sensitive_key(self.data):
            raise RuntimeContractError(
                "response data contains a raw sensitive field"
            )

        if self.error is not None:
            self.error.validate()
