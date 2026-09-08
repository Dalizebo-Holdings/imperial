from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

try:
    from .credential_reference import CredentialContext
    from .runtime_contract import (
        ConnectorResponse,
        NormalizedConnectorError,
        PreparedConnectorCall,
        RuntimeContractError,
    )
except ImportError:
    from credential_reference import CredentialContext
    from runtime_contract import (
        ConnectorResponse,
        NormalizedConnectorError,
        PreparedConnectorCall,
        RuntimeContractError,
    )


class ProviderAdapterError(ValueError):
    pass


@dataclass(frozen=True)
class AdapterHealth:
    healthy: bool
    status: str
    details: dict[str, Any]


class ProviderAdapter(ABC):
    connector_id: str
    connector_version: str
    adapter_version: str
    supported_operations: set[str]

    def validate_identity(self) -> None:
        for name in (
            "connector_id",
            "connector_version",
            "adapter_version",
        ):
            value = str(getattr(self, name, "")).strip()

            if not value:
                raise ProviderAdapterError(
                    f"{name} must not be empty"
                )

        if not self.supported_operations:
            raise ProviderAdapterError(
                "supported_operations must not be empty"
            )

    def validate_context(
        self,
        *,
        prepared_call: PreparedConnectorCall,
        credential_context: CredentialContext,
    ) -> None:
        self.validate_identity()

        connector = prepared_call.connector
        request = prepared_call.request

        if prepared_call.state != "READY_FOR_ADAPTER_EXECUTION":
            raise ProviderAdapterError(
                "prepared call is not ready for adapter execution"
            )

        if connector.connector_id != self.connector_id:
            raise ProviderAdapterError(
                "adapter connector_id mismatch"
            )

        if connector.version != self.connector_version:
            raise ProviderAdapterError(
                "adapter connector_version mismatch"
            )

        if request.operation not in self.supported_operations:
            raise ProviderAdapterError(
                f"adapter does not support operation: {request.operation}"
            )

        if credential_context.organization_id != request.organization_id:
            raise ProviderAdapterError(
                "credential context organization mismatch"
            )

        if credential_context.connector_id != connector.connector_id:
            raise ProviderAdapterError(
                "credential context connector mismatch"
            )

        if credential_context.auth_method != request.auth_method:
            raise ProviderAdapterError(
                "credential context authentication mismatch"
            )

        if credential_context.credential_ref != request.credential_ref:
            raise ProviderAdapterError(
                "credential context reference mismatch"
            )

        undeclared = sorted(
            set(request.permission_scopes)
            - set(credential_context.approved_scopes)
        )

        if undeclared:
            raise ProviderAdapterError(
                "credential context missing approved scopes: "
                + ", ".join(undeclared)
            )

    @abstractmethod
    def execute(
        self,
        *,
        prepared_call: PreparedConnectorCall,
        credential_context: CredentialContext,
    ) -> ConnectorResponse:
        """Execute one provider operation.

        Concrete production implementations own the network boundary.
        The base interface performs no network calls.
        """
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> AdapterHealth:
        raise NotImplementedError


def normalize_adapter_exception(
    *,
    prepared_call: PreparedConnectorCall,
    exc: Exception,
    retryable: bool = False,
    provider_code: str | None = None,
) -> ConnectorResponse:
    request = prepared_call.request

    error = NormalizedConnectorError(
        code="PROVIDER_ADAPTER_ERROR",
        message="Provider adapter operation failed",
        provider_code=provider_code,
        retryable=retryable,
        category="PROVIDER",
    )
    error.validate()

    response = ConnectorResponse(
        request_id=request.request_id,
        connector_id=request.connector_id,
        correlation_id=request.correlation_id,
        status="ERROR",
        provider_status=None,
        data=None,
        error=error,
        retryable=retryable,
        rate_limit={},
        audit_event={
            "event_type": "integrations_os.connector.error",
            "request_id": request.request_id,
            "connector_id": request.connector_id,
            "correlation_id": request.correlation_id,
            "error_code": error.code,
            "retryable": retryable,
        },
    )
    response.validate()
    return response


class ProviderAdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[tuple[str, str], ProviderAdapter] = {}

    def register(
        self,
        adapter: ProviderAdapter,
        *,
        replace_existing: bool = False,
    ) -> None:
        adapter.validate_identity()
        key = (
            adapter.connector_id,
            adapter.connector_version,
        )

        if key in self._adapters and not replace_existing:
            raise ProviderAdapterError(
                f"provider adapter already registered: {key[0]}@{key[1]}"
            )

        self._adapters[key] = adapter

    def get(
        self,
        connector_id: str,
        connector_version: str,
    ) -> ProviderAdapter:
        key = (
            str(connector_id).strip(),
            str(connector_version).strip(),
        )
        adapter = self._adapters.get(key)

        if adapter is None:
            raise ProviderAdapterError(
                f"provider adapter not registered: {key[0]}@{key[1]}"
            )

        return adapter

    def prepare_adapter(
        self,
        *,
        prepared_call: PreparedConnectorCall,
        credential_context: CredentialContext,
    ) -> ProviderAdapter:
        adapter = self.get(
            prepared_call.connector.connector_id,
            prepared_call.connector.version,
        )

        adapter.validate_context(
            prepared_call=prepared_call,
            credential_context=credential_context,
        )

        return adapter
