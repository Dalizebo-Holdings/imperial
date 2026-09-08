from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
import hashlib
import hmac
import ipaddress
import json
import re
from typing import Any
from urllib.parse import urlsplit


DELIVERY_STATES = {
    "PENDING",
    "DELIVERED",
    "RETRY_PENDING",
    "DEAD_LETTER",
}

SECRET_REF_PATTERN = re.compile(
    r"(?:secret|vault|kms)://[A-Za-z0-9._~:/-]+"
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
}


class WebhooksBaaSError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    result = str(value).strip()
    if not result:
        raise WebhooksBaaSError(
            f"{name} must not be empty"
        )
    return result


def _time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise WebhooksBaaSError(
            "timestamp must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise WebhooksBaaSError(
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


def validate_webhook_url(value: str) -> str:
    raw = _text("url", value)
    parsed = urlsplit(raw)

    if parsed.scheme.lower() != "https":
        raise WebhooksBaaSError(
            "webhook URL must use HTTPS"
        )

    if parsed.username or parsed.password:
        raise WebhooksBaaSError(
            "webhook URL userinfo is forbidden"
        )

    host = parsed.hostname

    if not host:
        raise WebhooksBaaSError(
            "webhook URL hostname is required"
        )

    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None

    if address is not None:
        if (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_reserved
            or address.is_unspecified
        ):
            raise WebhooksBaaSError(
                "webhook URL may not target non-public IP literals"
            )

    if parsed.fragment:
        raise WebhooksBaaSError(
            "webhook URL fragments are forbidden"
        )

    return raw


def event_pattern_matches(
    pattern: str,
    event_type: str,
) -> bool:
    pattern = _text(
        "event_pattern",
        pattern,
    )
    event_type = _text(
        "event_type",
        event_type,
    )

    if pattern == "*":
        return True

    if pattern.endswith(".*"):
        prefix = pattern[:-1]
        return event_type.startswith(
            prefix
        )

    return pattern == event_type


def sign_payload(
    *,
    raw_body: bytes,
    raw_secret: bytes,
    timestamp: str,
) -> str:
    if not isinstance(raw_body, bytes):
        raise WebhooksBaaSError(
            "raw_body must be bytes"
        )

    if not isinstance(raw_secret, bytes):
        raise WebhooksBaaSError(
            "raw_secret must be bytes"
        )

    if len(raw_secret) < 32:
        raise WebhooksBaaSError(
            "raw_secret must contain at least 32 bytes"
        )

    _time(timestamp)

    signing_input = (
        timestamp.encode("utf-8")
        + b"."
        + raw_body
    )

    digest = hmac.new(
        raw_secret,
        signing_input,
        hashlib.sha256,
    ).hexdigest()

    return "sha256=" + digest


def verify_signature(
    *,
    raw_body: bytes,
    raw_secret: bytes,
    timestamp: str,
    supplied_signature: str,
) -> bool:
    expected = sign_payload(
        raw_body=raw_body,
        raw_secret=raw_secret,
        timestamp=timestamp,
    )

    return hmac.compare_digest(
        expected,
        str(supplied_signature),
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
class WebhookEndpoint:
    endpoint_id: str
    tenant: TenantScope
    url: str
    event_patterns: tuple[str, ...]
    signing_secret_ref: str
    signing_secret_version: int
    timeout_seconds: int
    max_attempts: int
    enabled: bool = True

    def validate(self) -> None:
        _text(
            "endpoint_id",
            self.endpoint_id,
        )
        self.tenant.validate()
        validate_webhook_url(
            self.url
        )

        if not self.event_patterns:
            raise WebhooksBaaSError(
                "event_patterns must not be empty"
            )

        if len(
            self.event_patterns
        ) != len(
            set(self.event_patterns)
        ):
            raise WebhooksBaaSError(
                "event_patterns contains duplicates"
            )

        for pattern in self.event_patterns:
            if pattern != "*":
                if pattern.endswith(".*"):
                    prefix = pattern[:-2]
                    if not re.fullmatch(
                        r"[a-z0-9][a-z0-9._-]*",
                        prefix,
                    ):
                        raise WebhooksBaaSError(
                            "invalid wildcard event pattern"
                        )
                elif not re.fullmatch(
                    r"[a-z0-9][a-z0-9._-]*",
                    pattern,
                ):
                    raise WebhooksBaaSError(
                        "invalid event pattern"
                    )

        if not SECRET_REF_PATTERN.fullmatch(
            str(
                self.signing_secret_ref
            ).strip()
        ):
            raise WebhooksBaaSError(
                "signing_secret_ref must be an opaque secret reference"
            )

        if (
            not isinstance(
                self.signing_secret_version,
                int,
            )
            or self.signing_secret_version < 1
        ):
            raise WebhooksBaaSError(
                "signing_secret_version must be >= 1"
            )

        if (
            not isinstance(
                self.timeout_seconds,
                int,
            )
            or self.timeout_seconds < 1
            or self.timeout_seconds > 120
        ):
            raise WebhooksBaaSError(
                "timeout_seconds must be 1..120"
            )

        if (
            not isinstance(
                self.max_attempts,
                int,
            )
            or self.max_attempts < 1
            or self.max_attempts > 25
        ):
            raise WebhooksBaaSError(
                "max_attempts must be 1..25"
            )

    def matches(
        self,
        event_type: str,
    ) -> bool:
        return any(
            event_pattern_matches(
                pattern,
                event_type,
            )
            for pattern in self.event_patterns
        )


@dataclass(frozen=True)
class WebhookEvent:
    event_id: str
    event_type: str
    tenant: TenantScope
    correlation_id: str
    payload: dict[str, Any]
    occurred_at: str

    def validate(self) -> None:
        for name, value in {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "correlation_id": self.correlation_id,
        }.items():
            _text(name, value)

        self.tenant.validate()
        _time(self.occurred_at)

        try:
            json.dumps(
                self.payload,
                sort_keys=True,
                separators=(",", ":"),
            )
        except (TypeError, ValueError) as exc:
            raise WebhooksBaaSError(
                "payload must be JSON-compatible"
            ) from exc

        if _contains_sensitive(
            self.payload
        ):
            raise WebhooksBaaSError(
                "webhook payload contains secret-bearing fields"
            )


@dataclass(frozen=True)
class WebhookDelivery:
    delivery_id: str
    endpoint_id: str
    event_id: str
    state: str
    attempt: int
    max_attempts: int
    replay_of: str | None = None
    replay_sequence: int = 0
    replay_reason: str | None = None
    last_http_status: int | None = None
    last_error_code: str | None = None

    def validate(self) -> None:
        for name, value in {
            "delivery_id": self.delivery_id,
            "endpoint_id": self.endpoint_id,
            "event_id": self.event_id,
        }.items():
            _text(name, value)

        if self.state not in DELIVERY_STATES:
            raise WebhooksBaaSError(
                f"invalid delivery state: {self.state}"
            )

        if (
            not isinstance(self.attempt, int)
            or self.attempt < 1
            or self.attempt > self.max_attempts
        ):
            raise WebhooksBaaSError(
                "attempt must be within 1..max_attempts"
            )

        if (
            not isinstance(
                self.replay_sequence,
                int,
            )
            or self.replay_sequence < 0
        ):
            raise WebhooksBaaSError(
                "replay_sequence must be >= 0"
            )


@dataclass(frozen=True)
class WebhookDeliveryPlan:
    delivery_id: str
    endpoint_id: str
    event_id: str
    url: str
    timeout_seconds: int
    attempt: int
    signing_secret_ref: str
    signing_secret_version: int
    tenant_context: dict[str, str]
    correlation_id: str
    request_headers: dict[str, str]
    audit_event: dict[str, Any]
    log_context: dict[str, Any]
    delivery_state: str = "READY_FOR_HTTPS_ADAPTER"


class WebhooksManager:
    def __init__(self) -> None:
        self._endpoints: dict[
            str,
            WebhookEndpoint,
        ] = {}
        self._events: dict[
            str,
            WebhookEvent,
        ] = {}
        self._deliveries: dict[
            str,
            WebhookDelivery,
        ] = {}
        self._replay_counters: dict[
            str,
            int,
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
            raise WebhooksBaaSError(
                "webhook operations require Kernel authorization evidence"
            )

    @staticmethod
    def _same_tenant(
        tenant: TenantScope,
        request_context: Any,
    ) -> bool:
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

    @staticmethod
    def _tenant_equal(
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

    def register_endpoint(
        self,
        *,
        endpoint: WebhookEndpoint,
        request_context: Any,
    ) -> None:
        self._validate_request_context(
            request_context
        )
        endpoint.validate()

        if not self._same_tenant(
            endpoint.tenant,
            request_context,
        ):
            raise WebhooksBaaSError(
                "endpoint tenant scope mismatch"
            )

        if (
            endpoint.endpoint_id
            in self._endpoints
        ):
            raise WebhooksBaaSError(
                "endpoint already registered"
            )

        self._endpoints[
            endpoint.endpoint_id
        ] = endpoint

    def rotate_signing_secret(
        self,
        *,
        endpoint_id: str,
        new_secret_ref: str,
        request_context: Any,
    ) -> WebhookEndpoint:
        endpoint = self._get_endpoint(
            endpoint_id=endpoint_id,
            request_context=request_context,
        )

        if not SECRET_REF_PATTERN.fullmatch(
            str(new_secret_ref).strip()
        ):
            raise WebhooksBaaSError(
                "new_secret_ref must be an opaque secret reference"
            )

        if (
            new_secret_ref
            == endpoint.signing_secret_ref
        ):
            raise WebhooksBaaSError(
                "secret rotation requires a new secret reference"
            )

        updated = replace(
            endpoint,
            signing_secret_ref=(
                new_secret_ref
            ),
            signing_secret_version=(
                endpoint.signing_secret_version
                + 1
            ),
        )
        updated.validate()

        self._endpoints[
            endpoint_id
        ] = updated

        return updated

    def plan_event(
        self,
        *,
        event: WebhookEvent,
        request_context: Any,
    ) -> list[WebhookDeliveryPlan]:
        self._validate_request_context(
            request_context
        )
        event.validate()

        if not self._same_tenant(
            event.tenant,
            request_context,
        ):
            raise WebhooksBaaSError(
                "event tenant scope mismatch"
            )

        existing = self._events.get(
            event.event_id
        )

        if existing is not None:
            old = json.dumps(
                existing.payload,
                sort_keys=True,
                separators=(",", ":"),
            )
            new = json.dumps(
                event.payload,
                sort_keys=True,
                separators=(",", ":"),
            )

            if (
                existing.event_type
                != event.event_type
                or old != new
            ):
                raise WebhooksBaaSError(
                    "event_id content conflict"
                )

        self._events[
            event.event_id
        ] = event

        plans: list[
            WebhookDeliveryPlan
        ] = []

        for endpoint in sorted(
            self._endpoints.values(),
            key=lambda item: (
                item.endpoint_id
            ),
        ):
            if not endpoint.enabled:
                continue

            if not self._tenant_equal(
                endpoint.tenant,
                event.tenant,
            ):
                continue

            if not endpoint.matches(
                event.event_type
            ):
                continue

            delivery_id = (
                self._initial_delivery_id(
                    event.event_id,
                    endpoint.endpoint_id,
                )
            )

            record = self._deliveries.get(
                delivery_id
            )

            if record is None:
                record = WebhookDelivery(
                    delivery_id=delivery_id,
                    endpoint_id=(
                        endpoint.endpoint_id
                    ),
                    event_id=(
                        event.event_id
                    ),
                    state="PENDING",
                    attempt=1,
                    max_attempts=(
                        endpoint.max_attempts
                    ),
                )
                record.validate()
                self._deliveries[
                    delivery_id
                ] = record

            if record.state == "DELIVERED":
                continue

            plans.append(
                self._plan(
                    event=event,
                    endpoint=endpoint,
                    record=record,
                )
            )

        return plans

    def record_result(
        self,
        *,
        delivery_id: str,
        success: bool,
        http_status: int | None,
        error_code: str | None = None,
    ) -> WebhookDelivery:
        record = self._require_delivery(
            delivery_id
        )

        if record.state in {
            "DELIVERED",
            "DEAD_LETTER",
        }:
            raise WebhooksBaaSError(
                "terminal delivery cannot be updated"
            )

        if http_status is not None:
            if (
                not isinstance(
                    http_status,
                    int,
                )
                or http_status < 100
                or http_status > 599
            ):
                raise WebhooksBaaSError(
                    "http_status must be 100..599"
                )

        if success:
            updated = replace(
                record,
                state="DELIVERED",
                last_http_status=(
                    http_status
                ),
                last_error_code=None,
            )
        else:
            code = _text(
                "error_code",
                error_code,
            )

            if (
                record.attempt
                >= record.max_attempts
            ):
                state = "DEAD_LETTER"
                next_attempt = (
                    record.attempt
                )
            else:
                state = "RETRY_PENDING"
                next_attempt = (
                    record.attempt + 1
                )

            updated = replace(
                record,
                state=state,
                attempt=next_attempt,
                last_http_status=(
                    http_status
                ),
                last_error_code=code,
            )

        updated.validate()
        self._deliveries[
            delivery_id
        ] = updated

        return updated

    def retry_plan(
        self,
        *,
        delivery_id: str,
        request_context: Any,
    ) -> WebhookDeliveryPlan:
        record = self._require_delivery(
            delivery_id
        )

        if record.state != "RETRY_PENDING":
            raise WebhooksBaaSError(
                "delivery is not retry-pending"
            )

        event = self._events.get(
            record.event_id
        )

        if event is None:
            raise WebhooksBaaSError(
                "delivery event is missing"
            )

        endpoint = self._get_endpoint(
            endpoint_id=(
                record.endpoint_id
            ),
            request_context=request_context,
        )

        return self._plan(
            event=event,
            endpoint=endpoint,
            record=record,
        )

    def replay(
        self,
        *,
        delivery_id: str,
        reason: str,
        request_context: Any,
    ) -> WebhookDeliveryPlan:
        original = self._require_delivery(
            delivery_id
        )

        if original.state not in {
            "DELIVERED",
            "DEAD_LETTER",
        }:
            raise WebhooksBaaSError(
                "only terminal deliveries may be replayed"
            )

        replay_reason = _text(
            "reason",
            reason,
        )

        endpoint = self._get_endpoint(
            endpoint_id=(
                original.endpoint_id
            ),
            request_context=request_context,
        )
        event = self._events.get(
            original.event_id
        )

        if event is None:
            raise WebhooksBaaSError(
                "delivery event is missing"
            )

        counter = (
            self._replay_counters.get(
                delivery_id,
                0,
            )
            + 1
        )
        self._replay_counters[
            delivery_id
        ] = counter

        replay_id = (
            "whdel_"
            + sha256(
                (
                    f"{delivery_id}"
                    f"\x1freplay\x1f"
                    f"{counter}"
                ).encode("utf-8")
            ).hexdigest()[:24]
        )

        record = WebhookDelivery(
            delivery_id=replay_id,
            endpoint_id=(
                original.endpoint_id
            ),
            event_id=(
                original.event_id
            ),
            state="PENDING",
            attempt=1,
            max_attempts=(
                endpoint.max_attempts
            ),
            replay_of=(
                original.delivery_id
            ),
            replay_sequence=counter,
            replay_reason=replay_reason,
        )
        record.validate()

        self._deliveries[
            replay_id
        ] = record

        return self._plan(
            event=event,
            endpoint=endpoint,
            record=record,
        )

    def _get_endpoint(
        self,
        *,
        endpoint_id: str,
        request_context: Any,
    ) -> WebhookEndpoint:
        self._validate_request_context(
            request_context
        )

        endpoint = self._endpoints.get(
            str(endpoint_id).strip()
        )

        if endpoint is None:
            raise WebhooksBaaSError(
                "endpoint not found"
            )

        if not self._same_tenant(
            endpoint.tenant,
            request_context,
        ):
            raise WebhooksBaaSError(
                "cross-tenant endpoint access denied"
            )

        return endpoint

    def _require_delivery(
        self,
        delivery_id: str,
    ) -> WebhookDelivery:
        record = self._deliveries.get(
            str(delivery_id).strip()
        )

        if record is None:
            raise WebhooksBaaSError(
                "delivery not found"
            )

        return record

    @staticmethod
    def _initial_delivery_id(
        event_id: str,
        endpoint_id: str,
    ) -> str:
        material = (
            f"{event_id}"
            f"\x1f{endpoint_id}"
        )

        return (
            "whdel_"
            + sha256(
                material.encode("utf-8")
            ).hexdigest()[:24]
        )

    @staticmethod
    def _plan(
        *,
        event: WebhookEvent,
        endpoint: WebhookEndpoint,
        record: WebhookDelivery,
    ) -> WebhookDeliveryPlan:
        return WebhookDeliveryPlan(
            delivery_id=(
                record.delivery_id
            ),
            endpoint_id=(
                endpoint.endpoint_id
            ),
            event_id=(
                event.event_id
            ),
            url=endpoint.url,
            timeout_seconds=(
                endpoint.timeout_seconds
            ),
            attempt=record.attempt,
            signing_secret_ref=(
                endpoint.signing_secret_ref
            ),
            signing_secret_version=(
                endpoint.signing_secret_version
            ),
            tenant_context={
                "organization_id": (
                    endpoint.tenant.organization_id
                ),
                "workspace_id": (
                    endpoint.tenant.workspace_id
                ),
                "project_id": (
                    endpoint.tenant.project_id
                ),
                "environment_id": (
                    endpoint.tenant.environment_id
                ),
            },
            correlation_id=(
                event.correlation_id
            ),
            request_headers={
                "X-Dalizebo-Webhook-Id": (
                    record.delivery_id
                ),
                "X-Dalizebo-Webhook-Secret-Version": (
                    str(
                        endpoint.signing_secret_version
                    )
                ),
            },
            audit_event={
                "event_type": (
                    "baas.webhook.delivery_planned"
                ),
                "delivery_id": (
                    record.delivery_id
                ),
                "event_id": (
                    event.event_id
                ),
                "endpoint_id": (
                    endpoint.endpoint_id
                ),
                "attempt": (
                    record.attempt
                ),
                "correlation_id": (
                    event.correlation_id
                ),
            },
            log_context={
                "delivery_id": (
                    record.delivery_id
                ),
                "endpoint_id": (
                    endpoint.endpoint_id
                ),
                "event_id": (
                    event.event_id
                ),
                "organization_id": (
                    endpoint.tenant.organization_id
                ),
                "correlation_id": (
                    event.correlation_id
                ),
            },
        )
