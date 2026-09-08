from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any


FUNCTION_STATES = {
    "DRAFT",
    "ACTIVE",
    "SUSPENDED",
    "RETIRED",
}

STATE_TRANSITIONS = {
    "DRAFT": {"ACTIVE", "RETIRED"},
    "ACTIVE": {"SUSPENDED", "RETIRED"},
    "SUSPENDED": {"ACTIVE", "RETIRED"},
    "RETIRED": set(),
}

TRIGGER_TYPES = {
    "HTTP",
    "EVENT",
    "SCHEDULED",
    "MANUAL",
}

HTTP_METHODS = {
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
}

RUNTIME_PATTERN = re.compile(
    r"[a-z][a-z0-9._-]{1,63}"
)

CODE_REF_PATTERN = re.compile(
    r"(?:object|storage|artifact)://[A-Za-z0-9._~:/-]+"
)

SECRET_REF_PATTERN = re.compile(
    r"(?:secret|vault|kms)://[A-Za-z0-9._~:/-]+"
)

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
    "session_token",
    "webhook_secret",
    "provider_credentials",
}


class FunctionsBaaSError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    result = str(value).strip()
    if not result:
        raise FunctionsBaaSError(
            f"{name} must not be empty"
        )
    return result


def _time(value: str | None = None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise FunctionsBaaSError(
            "timestamp must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise FunctionsBaaSError(
            "timestamp must be timezone-aware"
        )

    return parsed


def _contains_sensitive(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).strip().lower() in SENSITIVE_KEYS:
                return True
            if _contains_sensitive(item):
                return True
    elif isinstance(value, (list, tuple)):
        return any(
            _contains_sensitive(item)
            for item in value
        )
    return False


def _validate_metadata(
    metadata: dict[str, Any],
) -> None:
    try:
        json.dumps(
            metadata,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise FunctionsBaaSError(
            "metadata must be JSON-compatible"
        ) from exc

    if _contains_sensitive(metadata):
        raise FunctionsBaaSError(
            "metadata contains secret-bearing fields"
        )


@dataclass(frozen=True)
class TenantScope:
    organization_id: str
    workspace_id: str
    project_id: str
    environment_id: str

    def validate(self) -> None:
        for name, value in {
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "environment_id": self.environment_id,
        }.items():
            _text(name, value)


@dataclass(frozen=True)
class TriggerDefinition:
    trigger_type: str
    http_method: str | None = None
    http_path: str | None = None
    event_type: str | None = None
    schedule_expression: str | None = None

    def validate(self) -> None:
        trigger = str(self.trigger_type).strip().upper()

        if trigger not in TRIGGER_TYPES:
            raise FunctionsBaaSError(
                f"unsupported trigger_type: {trigger}"
            )

        if trigger == "HTTP":
            method = str(
                self.http_method or ""
            ).strip().upper()

            if method not in HTTP_METHODS:
                raise FunctionsBaaSError(
                    "HTTP trigger requires a supported method"
                )

            path = _text(
                "http_path",
                self.http_path,
            )

            if not path.startswith("/"):
                raise FunctionsBaaSError(
                    "http_path must begin with /"
                )

            if self.event_type or self.schedule_expression:
                raise FunctionsBaaSError(
                    "HTTP trigger contains incompatible fields"
                )

        elif trigger == "EVENT":
            _text(
                "event_type",
                self.event_type,
            )

            if (
                self.http_method
                or self.http_path
                or self.schedule_expression
            ):
                raise FunctionsBaaSError(
                    "EVENT trigger contains incompatible fields"
                )

        elif trigger == "SCHEDULED":
            _text(
                "schedule_expression",
                self.schedule_expression,
            )

            if (
                self.http_method
                or self.http_path
                or self.event_type
            ):
                raise FunctionsBaaSError(
                    "SCHEDULED trigger contains incompatible fields"
                )

        elif trigger == "MANUAL":
            if any(
                [
                    self.http_method,
                    self.http_path,
                    self.event_type,
                    self.schedule_expression,
                ]
            ):
                raise FunctionsBaaSError(
                    "MANUAL trigger may not define trigger-specific fields"
                )


@dataclass(frozen=True)
class FunctionDescriptor:
    function_id: str
    tenant: TenantScope
    name: str
    runtime: str
    entrypoint: str
    code_bundle_ref: str
    trigger: TriggerDefinition
    timeout_seconds: int
    memory_mb: int
    secret_refs: tuple[str, ...]
    state: str
    created_at: str
    updated_at: str

    def validate(self) -> None:
        _text(
            "function_id",
            self.function_id,
        )
        self.tenant.validate()
        _text("name", self.name)

        if not RUNTIME_PATTERN.fullmatch(
            str(self.runtime).strip()
        ):
            raise FunctionsBaaSError(
                "runtime must be a safe runtime identifier"
            )

        entrypoint = _text(
            "entrypoint",
            self.entrypoint,
        )

        if len(entrypoint) > 255:
            raise FunctionsBaaSError(
                "entrypoint exceeds 255 characters"
            )

        if not CODE_REF_PATTERN.fullmatch(
            str(self.code_bundle_ref).strip()
        ):
            raise FunctionsBaaSError(
                "code_bundle_ref must use object://, storage://, or artifact://"
            )

        self.trigger.validate()

        if (
            not isinstance(self.timeout_seconds, int)
            or self.timeout_seconds < 1
            or self.timeout_seconds > 900
        ):
            raise FunctionsBaaSError(
                "timeout_seconds must be 1..900"
            )

        if (
            not isinstance(self.memory_mb, int)
            or self.memory_mb < 128
            or self.memory_mb > 4096
        ):
            raise FunctionsBaaSError(
                "memory_mb must be 128..4096"
            )

        if len(self.secret_refs) > 64:
            raise FunctionsBaaSError(
                "secret_refs exceeds 64 entries"
            )

        normalized = []

        for ref in self.secret_refs:
            value = str(ref).strip()

            if not SECRET_REF_PATTERN.fullmatch(
                value
            ):
                raise FunctionsBaaSError(
                    "secret_refs must be opaque secret://, vault://, or kms:// references"
                )

            normalized.append(value)

        if len(normalized) != len(
            set(normalized)
        ):
            raise FunctionsBaaSError(
                "secret_refs contains duplicates"
            )

        if self.state not in FUNCTION_STATES:
            raise FunctionsBaaSError(
                f"invalid function state: {self.state}"
            )

        _time(self.created_at)
        _time(self.updated_at)


@dataclass(frozen=True)
class InvocationRequest:
    function_id: str
    trigger_type: str
    payload_metadata: dict[str, Any]
    requested_at: str

    def validate(self) -> None:
        _text(
            "function_id",
            self.function_id,
        )

        trigger = str(
            self.trigger_type
        ).strip().upper()

        if trigger not in TRIGGER_TYPES:
            raise FunctionsBaaSError(
                f"unsupported trigger_type: {trigger}"
            )

        _validate_metadata(
            self.payload_metadata
        )
        _time(self.requested_at)


@dataclass(frozen=True)
class InvocationPlan:
    execution_id: str
    function_id: str
    runtime: str
    entrypoint: str
    code_bundle_ref: str
    trigger_type: str
    timeout_seconds: int
    memory_mb: int
    secret_refs: tuple[str, ...]
    tenant_context: dict[str, str]
    correlation_id: str
    kernel_authorization_ref: str
    audit_event: dict[str, Any]
    log_context: dict[str, Any]
    execution_state: str = "READY_FOR_RUNTIME_ADAPTER"


class FunctionsManager:
    def __init__(self) -> None:
        self._functions: dict[
            str,
            FunctionDescriptor,
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
            "organization_id",
            "workspace_id",
            "project_id",
            "environment_id",
            "kernel_authorization_ref",
            "correlation_id",
            "actor_id",
        ]:
            _text(
                name,
                getattr(
                    request_context,
                    name,
                    None,
                ),
            )

        if not str(
            request_context.kernel_authorization_ref
        ).startswith("kernel_auth_"):
            raise FunctionsBaaSError(
                "function operations require Kernel authorization evidence"
            )

    @staticmethod
    def _same_tenant(
        function: FunctionDescriptor,
        request_context: Any,
    ) -> bool:
        tenant = function.tenant

        return (
            tenant.organization_id
            == request_context.organization_id
            and tenant.workspace_id
            == request_context.workspace_id
            and tenant.project_id
            == request_context.project_id
            and tenant.environment_id
            == request_context.environment_id
        )

    def register(
        self,
        *,
        function: FunctionDescriptor,
        request_context: Any,
    ) -> None:
        self._validate_request_context(
            request_context
        )
        function.validate()

        if not self._same_tenant(
            function,
            request_context,
        ):
            raise FunctionsBaaSError(
                "function tenant scope mismatch"
            )

        if (
            function.function_id
            in self._functions
        ):
            raise FunctionsBaaSError(
                "function already registered"
            )

        self._functions[
            function.function_id
        ] = function

    def get(
        self,
        *,
        function_id: str,
        request_context: Any,
    ) -> FunctionDescriptor:
        self._validate_request_context(
            request_context
        )

        function = self._functions.get(
            str(function_id).strip()
        )

        if function is None:
            raise FunctionsBaaSError(
                "function not found"
            )

        if not self._same_tenant(
            function,
            request_context,
        ):
            raise FunctionsBaaSError(
                "cross-tenant function access denied"
            )

        return function

    def transition(
        self,
        *,
        function_id: str,
        target_state: str,
        request_context: Any,
        now: str | None = None,
    ) -> FunctionDescriptor:
        function = self.get(
            function_id=function_id,
            request_context=request_context,
        )

        target = str(
            target_state
        ).strip().upper()

        if target not in FUNCTION_STATES:
            raise FunctionsBaaSError(
                f"invalid target state: {target}"
            )

        if target not in STATE_TRANSITIONS[
            function.state
        ]:
            raise FunctionsBaaSError(
                f"illegal function transition: {function.state} -> {target}"
            )

        updated = replace(
            function,
            state=target,
            updated_at=_time(
                now
            ).isoformat(),
        )
        updated.validate()

        self._functions[
            function.function_id
        ] = updated

        return updated

    def build_invocation_plan(
        self,
        *,
        invocation: InvocationRequest,
        request_context: Any,
    ) -> InvocationPlan:
        invocation.validate()

        function = self.get(
            function_id=invocation.function_id,
            request_context=request_context,
        )

        if function.state != "ACTIVE":
            raise FunctionsBaaSError(
                "function must be ACTIVE"
            )

        requested_trigger = str(
            invocation.trigger_type
        ).strip().upper()

        configured_trigger = str(
            function.trigger.trigger_type
        ).strip().upper()

        if (
            requested_trigger
            != configured_trigger
            and requested_trigger != "MANUAL"
        ):
            raise FunctionsBaaSError(
                "invocation trigger does not match function trigger"
            )

        material = {
            "function_id": function.function_id,
            "correlation_id": (
                request_context.correlation_id
            ),
            "requested_at": (
                invocation.requested_at
            ),
            "trigger_type": (
                requested_trigger
            ),
            "code_bundle_ref": (
                function.code_bundle_ref
            ),
        }

        encoded = json.dumps(
            material,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        execution_id = (
            "exec_"
            + sha256(
                encoded
            ).hexdigest()[:24]
        )

        audit_event = {
            "event_type": (
                "baas.function.invocation_planned"
            ),
            "execution_id": execution_id,
            "function_id": (
                function.function_id
            ),
            "organization_id": (
                function.tenant.organization_id
            ),
            "environment_id": (
                function.tenant.environment_id
            ),
            "correlation_id": (
                request_context.correlation_id
            ),
            "actor_id": (
                request_context.actor_id
            ),
            "trigger_type": (
                requested_trigger
            ),
        }

        log_context = {
            "execution_id": (
                execution_id
            ),
            "function_id": (
                function.function_id
            ),
            "correlation_id": (
                request_context.correlation_id
            ),
            "organization_id": (
                function.tenant.organization_id
            ),
        }

        return InvocationPlan(
            execution_id=execution_id,
            function_id=function.function_id,
            runtime=function.runtime,
            entrypoint=function.entrypoint,
            code_bundle_ref=(
                function.code_bundle_ref
            ),
            trigger_type=requested_trigger,
            timeout_seconds=(
                function.timeout_seconds
            ),
            memory_mb=function.memory_mb,
            secret_refs=(
                function.secret_refs
            ),
            tenant_context={
                "organization_id": (
                    function.tenant.organization_id
                ),
                "workspace_id": (
                    function.tenant.workspace_id
                ),
                "project_id": (
                    function.tenant.project_id
                ),
                "environment_id": (
                    function.tenant.environment_id
                ),
            },
            correlation_id=(
                request_context.correlation_id
            ),
            kernel_authorization_ref=(
                request_context.kernel_authorization_ref
            ),
            audit_event=audit_event,
            log_context=log_context,
        )
