from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import re
from typing import Any
from urllib.parse import urlsplit


API_PREFIX = "/api/v1"

HTTP_METHODS = {
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
}

TARGET_SERVICES = {
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
    "secrets",
    "backups",
}

SENSITIVE_KEYS = {
    "authorization",
    "cookie",
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


class GatewayError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        request_id: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.safe_message = message
        self.request_id = request_id
        self.details = details or {}

    def envelope(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.safe_message,
            "request_id": self.request_id,
            "details": _sanitize(self.details),
        }


def _text(name: str, value: Any) -> str:
    result = str(value).strip()
    if not result:
        raise ValueError(f"{name} must not be empty")
    return result


def _time(value: str | None = None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            "timestamp must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise ValueError(
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
        return any(_contains_sensitive(item) for item in value)
    return False


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        output = {}
        for key, item in value.items():
            if str(key).strip().lower() in SENSITIVE_KEYS:
                output[key] = "[REDACTED]"
            else:
                output[key] = _sanitize(item)
        return output
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize(item) for item in value]
    return value


def normalize_path(value: str) -> str:
    path = urlsplit(_text("path", value)).path

    if not path.startswith("/"):
        raise ValueError(
            "path must begin with /"
        )

    path = re.sub(r"/+", "/", path)

    if len(path) > 2048:
        raise ValueError(
            "path exceeds 2048 characters"
        )

    if not (
        path == API_PREFIX
        or path.startswith(API_PREFIX + "/")
    ):
        raise ValueError(
            "route path must be under /api/v1"
        )

    return path.rstrip("/") or "/"


@dataclass(frozen=True)
class GatewayRoute:
    route_id: str
    method: str
    path: str
    target_service: str
    target_operation: str
    authentication_required: bool
    required_permission: str | None
    max_payload_bytes: int
    timeout_ms: int
    rate_limit_requests: int
    rate_limit_window_seconds: int
    enabled: bool = True

    def validate(self) -> None:
        _text("route_id", self.route_id)

        method = str(self.method).strip().upper()
        if method not in HTTP_METHODS:
            raise ValueError(
                f"unsupported HTTP method: {method}"
            )

        normalize_path(self.path)

        service = str(
            self.target_service
        ).strip()

        if service not in TARGET_SERVICES:
            raise ValueError(
                f"unsupported target_service: {service}"
            )

        _text(
            "target_operation",
            self.target_operation,
        )

        if (
            self.required_permission is not None
            and not str(
                self.required_permission
            ).strip()
        ):
            raise ValueError(
                "required_permission cannot be blank"
            )

        if (
            self.required_permission is not None
            and not self.authentication_required
        ):
            raise ValueError(
                "permission-protected route must require authentication"
            )

        for name, value, maximum in [
            (
                "max_payload_bytes",
                self.max_payload_bytes,
                100 * 1024 * 1024,
            ),
            (
                "timeout_ms",
                self.timeout_ms,
                120000,
            ),
            (
                "rate_limit_requests",
                self.rate_limit_requests,
                1_000_000,
            ),
            (
                "rate_limit_window_seconds",
                self.rate_limit_window_seconds,
                86400,
            ),
        ]:
            if (
                not isinstance(value, int)
                or value < 1
                or value > maximum
            ):
                raise ValueError(
                    f"{name} must be an integer 1..{maximum}"
                )


@dataclass(frozen=True)
class GatewayRequest:
    request_id: str
    correlation_id: str
    method: str
    path: str
    content_length: int
    authenticated: bool
    actor_id: str | None
    actor_type: str | None
    kernel_authorization_ref: str | None
    permission_evidence: tuple[str, ...]
    organization_id: str
    workspace_id: str
    project_id: str
    environment_id: str
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def validate(self) -> None:
        for name, value in {
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "environment_id": self.environment_id,
        }.items():
            _text(name, value)

        method = str(
            self.method
        ).strip().upper()

        if method not in HTTP_METHODS:
            raise ValueError(
                f"unsupported HTTP method: {method}"
            )

        normalize_path(self.path)

        if (
            not isinstance(self.content_length, int)
            or self.content_length < 0
        ):
            raise ValueError(
                "content_length must be an integer >= 0"
            )

        if self.authenticated:
            _text("actor_id", self.actor_id)
            _text("actor_type", self.actor_type)

        if (
            self.kernel_authorization_ref is not None
            and not str(
                self.kernel_authorization_ref
            ).startswith("kernel_auth_")
        ):
            raise ValueError(
                "kernel_authorization_ref is invalid"
            )

        if len(self.permission_evidence) != len(
            set(self.permission_evidence)
        ):
            raise ValueError(
                "permission_evidence contains duplicates"
            )

        try:
            json.dumps(
                self.metadata,
                sort_keys=True,
                separators=(",", ":"),
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "metadata must be JSON-compatible"
            ) from exc

        if _contains_sensitive(
            self.metadata
        ):
            raise ValueError(
                "metadata contains secret-bearing fields"
            )


@dataclass(frozen=True)
class GatewayDispatchPlan:
    route_id: str
    target_service: str
    target_operation: str
    request_id: str
    correlation_id: str
    timeout_ms: int
    organization_id: str
    workspace_id: str
    project_id: str
    environment_id: str
    actor_id: str | None
    actor_type: str | None
    kernel_authorization_ref: str | None
    audit_event: dict[str, Any]
    log_context: dict[str, Any]
    dispatch_state: str = "READY_FOR_GATEWAY_ADAPTER"


class ReferenceRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[
            tuple[str, str, str],
            deque[datetime],
        ] = defaultdict(deque)

    def allow(
        self,
        *,
        route: GatewayRoute,
        request: GatewayRequest,
        now: str | None = None,
    ) -> bool:
        current = _time(now)
        actor = str(
            request.actor_id
            or "anonymous"
        )
        key = (
            route.route_id,
            request.organization_id,
            actor,
        )

        window_start = current - timedelta(
            seconds=route.rate_limit_window_seconds
        )

        hits = self._hits[key]

        while hits and hits[0] <= window_start:
            hits.popleft()

        if (
            len(hits)
            >= route.rate_limit_requests
        ):
            return False

        hits.append(current)
        return True


class APIGateway:
    def __init__(self) -> None:
        self._routes: dict[
            tuple[str, str],
            GatewayRoute,
        ] = {}
        self._route_ids: set[str] = set()
        self._rate_limiter = (
            ReferenceRateLimiter()
        )

    def register_route(
        self,
        route: GatewayRoute,
    ) -> None:
        route.validate()

        key = (
            str(route.method).strip().upper(),
            normalize_path(route.path),
        )

        if key in self._routes:
            raise ValueError(
                "route method/path already registered"
            )

        if route.route_id in self._route_ids:
            raise ValueError(
                "route_id already registered"
            )

        self._routes[key] = route
        self._route_ids.add(
            route.route_id
        )

    def resolve(
        self,
        *,
        request: GatewayRequest,
        now: str | None = None,
    ) -> GatewayDispatchPlan:
        try:
            request.validate()
        except Exception as exc:
            raise GatewayError(
                "INVALID_REQUEST",
                "Request validation failed",
                request_id=(
                    str(
                        getattr(
                            request,
                            "request_id",
                            "",
                        )
                    ).strip()
                    or "unknown"
                ),
            ) from exc

        key = (
            str(
                request.method
            ).strip().upper(),
            normalize_path(
                request.path
            ),
        )

        route = self._routes.get(key)

        if route is None:
            raise GatewayError(
                "ROUTE_NOT_FOUND",
                "Requested API route was not found",
                request_id=request.request_id,
            )

        if not route.enabled:
            raise GatewayError(
                "ROUTE_DISABLED",
                "Requested API route is unavailable",
                request_id=request.request_id,
            )

        if (
            request.content_length
            > route.max_payload_bytes
        ):
            raise GatewayError(
                "PAYLOAD_TOO_LARGE",
                "Request payload exceeds route limit",
                request_id=request.request_id,
                details={
                    "max_payload_bytes": (
                        route.max_payload_bytes
                    )
                },
            )

        if (
            route.authentication_required
            and not request.authenticated
        ):
            raise GatewayError(
                "AUTHENTICATION_REQUIRED",
                "Authentication is required",
                request_id=request.request_id,
            )

        if route.required_permission:
            if not request.kernel_authorization_ref:
                raise GatewayError(
                    "AUTHORIZATION_REQUIRED",
                    "Authorization evidence is required",
                    request_id=request.request_id,
                )

            if (
                route.required_permission
                not in request.permission_evidence
            ):
                raise GatewayError(
                    "PERMISSION_DENIED",
                    "Required permission was not granted",
                    request_id=request.request_id,
                )

        if not self._rate_limiter.allow(
            route=route,
            request=request,
            now=now,
        ):
            raise GatewayError(
                "RATE_LIMITED",
                "Request rate limit exceeded",
                request_id=request.request_id,
                details={
                    "window_seconds": (
                        route.rate_limit_window_seconds
                    ),
                    "limit": (
                        route.rate_limit_requests
                    ),
                },
            )

        material = {
            "route_id": route.route_id,
            "request_id": request.request_id,
            "correlation_id": (
                request.correlation_id
            ),
            "organization_id": (
                request.organization_id
            ),
            "actor_id": (
                request.actor_id
            ),
        }

        digest = sha256(
            json.dumps(
                material,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        audit_event = {
            "event_type": (
                "baas.api_gateway.route_resolved"
            ),
            "dispatch_ref": (
                "gateway_"
                + digest[:24]
            ),
            "route_id": (
                route.route_id
            ),
            "organization_id": (
                request.organization_id
            ),
            "actor_id": (
                request.actor_id
            ),
            "correlation_id": (
                request.correlation_id
            ),
        }

        log_context = {
            "route_id": route.route_id,
            "request_id": (
                request.request_id
            ),
            "correlation_id": (
                request.correlation_id
            ),
            "organization_id": (
                request.organization_id
            ),
            "target_service": (
                route.target_service
            ),
        }

        return GatewayDispatchPlan(
            route_id=route.route_id,
            target_service=(
                route.target_service
            ),
            target_operation=(
                route.target_operation
            ),
            request_id=request.request_id,
            correlation_id=(
                request.correlation_id
            ),
            timeout_ms=route.timeout_ms,
            organization_id=(
                request.organization_id
            ),
            workspace_id=(
                request.workspace_id
            ),
            project_id=(
                request.project_id
            ),
            environment_id=(
                request.environment_id
            ),
            actor_id=request.actor_id,
            actor_type=(
                request.actor_type
            ),
            kernel_authorization_ref=(
                request.kernel_authorization_ref
            ),
            audit_event=audit_event,
            log_context=log_context,
        )
