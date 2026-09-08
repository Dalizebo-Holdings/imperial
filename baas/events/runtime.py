from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any


DELIVERY_STATES = {
    "PENDING",
    "DELIVERED",
    "RETRY_PENDING",
    "DEAD_LETTER",
}

TARGET_TYPES = {
    "FUNCTION",
    "WEBHOOK",
    "INTERNAL",
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


class EventsBaaSError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    result = str(value).strip()
    if not result:
        raise EventsBaaSError(
            f"{name} must not be empty"
        )
    return result


def _time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise EventsBaaSError(
            "timestamp must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise EventsBaaSError(
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


def _validate_json(
    name: str,
    value: Any,
) -> None:
    try:
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise EventsBaaSError(
            f"{name} must be JSON-compatible"
        ) from exc


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
class EventEnvelope:
    event_id: str
    event_type: str
    event_version: str
    tenant: TenantScope
    resource_type: str
    resource_id: str
    occurred_at: str
    correlation_id: str
    actor_type: str
    actor_id: str
    payload: dict[str, Any]

    def validate(self) -> None:
        for name, value in {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "event_version": self.event_version,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "correlation_id": self.correlation_id,
            "actor_type": self.actor_type,
            "actor_id": self.actor_id,
        }.items():
            _text(name, value)

        self.tenant.validate()
        _time(self.occurred_at)
        _validate_json(
            "payload",
            self.payload,
        )

        if _contains_sensitive(
            self.payload
        ):
            raise EventsBaaSError(
                "event payload contains secret-bearing fields"
            )


@dataclass(frozen=True)
class OutboxEvent:
    event: EventEnvelope
    outbox_status: str

    def validate(self) -> None:
        self.event.validate()

        if self.outbox_status != "COMMITTED":
            raise EventsBaaSError(
                "events may only be published from COMMITTED outbox records"
            )


@dataclass(frozen=True)
class Subscription:
    subscription_id: str
    tenant: TenantScope
    event_pattern: str
    target_type: str
    target_ref: str
    max_attempts: int
    enabled: bool = True

    def validate(self) -> None:
        _text(
            "subscription_id",
            self.subscription_id,
        )
        self.tenant.validate()

        pattern = _text(
            "event_pattern",
            self.event_pattern,
        )

        if pattern != "*":
            if pattern.endswith(".*"):
                prefix = pattern[:-2]
                if not re.fullmatch(
                    r"[a-z0-9][a-z0-9._-]*",
                    prefix,
                ):
                    raise EventsBaaSError(
                        "invalid wildcard event_pattern"
                    )
            elif not re.fullmatch(
                r"[a-z0-9][a-z0-9._-]*",
                pattern,
            ):
                raise EventsBaaSError(
                    "invalid event_pattern"
                )

        if self.target_type not in TARGET_TYPES:
            raise EventsBaaSError(
                f"unsupported target_type: {self.target_type}"
            )

        _text(
            "target_ref",
            self.target_ref,
        )

        if (
            not isinstance(self.max_attempts, int)
            or self.max_attempts < 1
            or self.max_attempts > 25
        ):
            raise EventsBaaSError(
                "max_attempts must be 1..25"
            )

    def matches(
        self,
        event_type: str,
    ) -> bool:
        self.validate()
        event_type = _text(
            "event_type",
            event_type,
        )

        if self.event_pattern == "*":
            return True

        if self.event_pattern.endswith(".*"):
            prefix = (
                self.event_pattern[:-1]
            )
            return event_type.startswith(
                prefix
            )

        return (
            event_type
            == self.event_pattern
        )


@dataclass(frozen=True)
class DeliveryRecord:
    delivery_id: str
    event_id: str
    subscription_id: str
    state: str
    attempt: int
    max_attempts: int
    last_error_code: str | None = None

    def validate(self) -> None:
        for name, value in {
            "delivery_id": self.delivery_id,
            "event_id": self.event_id,
            "subscription_id": self.subscription_id,
        }.items():
            _text(name, value)

        if self.state not in DELIVERY_STATES:
            raise EventsBaaSError(
                f"invalid delivery state: {self.state}"
            )

        if (
            not isinstance(self.attempt, int)
            or self.attempt < 1
        ):
            raise EventsBaaSError(
                "attempt must be >= 1"
            )

        if (
            not isinstance(self.max_attempts, int)
            or self.max_attempts < 1
        ):
            raise EventsBaaSError(
                "max_attempts must be >= 1"
            )

        if self.attempt > self.max_attempts:
            raise EventsBaaSError(
                "attempt exceeds max_attempts"
            )


@dataclass(frozen=True)
class DeliveryPlan:
    delivery_id: str
    event_id: str
    subscription_id: str
    target_type: str
    target_ref: str
    attempt: int
    tenant_context: dict[str, str]
    correlation_id: str
    audit_event: dict[str, Any]
    log_context: dict[str, Any]
    delivery_state: str = "READY_FOR_DELIVERY_ADAPTER"


class EventsManager:
    def __init__(self) -> None:
        self._subscriptions: dict[
            str,
            Subscription,
        ] = {}
        self._events: dict[
            str,
            EventEnvelope,
        ] = {}
        self._event_hashes: dict[
            str,
            str,
        ] = {}
        self._deliveries: dict[
            str,
            DeliveryRecord,
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
            raise EventsBaaSError(
                "event operations require Kernel authorization evidence"
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

    def register_subscription(
        self,
        *,
        subscription: Subscription,
        request_context: Any,
    ) -> None:
        self._validate_request_context(
            request_context
        )
        subscription.validate()

        if not self._same_tenant(
            subscription.tenant,
            request_context,
        ):
            raise EventsBaaSError(
                "subscription tenant scope mismatch"
            )

        if (
            subscription.subscription_id
            in self._subscriptions
        ):
            raise EventsBaaSError(
                "subscription already registered"
            )

        self._subscriptions[
            subscription.subscription_id
        ] = subscription

    def publish_committed(
        self,
        *,
        outbox_event: OutboxEvent,
        request_context: Any,
    ) -> list[DeliveryPlan]:
        self._validate_request_context(
            request_context
        )
        outbox_event.validate()

        event = outbox_event.event

        if not self._same_tenant(
            event.tenant,
            request_context,
        ):
            raise EventsBaaSError(
                "event tenant scope mismatch"
            )

        canonical = json.dumps(
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "event_version": event.event_version,
                "organization_id": (
                    event.tenant.organization_id
                ),
                "workspace_id": (
                    event.tenant.workspace_id
                ),
                "project_id": (
                    event.tenant.project_id
                ),
                "environment_id": (
                    event.tenant.environment_id
                ),
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "occurred_at": event.occurred_at,
                "correlation_id": event.correlation_id,
                "actor_type": event.actor_type,
                "actor_id": event.actor_id,
                "payload": event.payload,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

        event_hash = sha256(
            canonical.encode("utf-8")
        ).hexdigest()

        existing_hash = (
            self._event_hashes.get(
                event.event_id
            )
        )

        if (
            existing_hash is not None
            and existing_hash != event_hash
        ):
            raise EventsBaaSError(
                "event_id content conflict"
            )

        self._events[
            event.event_id
        ] = event
        self._event_hashes[
            event.event_id
        ] = event_hash

        plans: list[
            DeliveryPlan
        ] = []

        for subscription in sorted(
            self._subscriptions.values(),
            key=lambda item: (
                item.subscription_id
            ),
        ):
            if not subscription.enabled:
                continue

            if not self._tenant_equal(
                subscription.tenant,
                event.tenant,
            ):
                continue

            if not subscription.matches(
                event.event_type
            ):
                continue

            delivery_id = self._delivery_id(
                event.event_id,
                subscription.subscription_id,
            )

            existing = self._deliveries.get(
                delivery_id
            )

            if existing is not None:
                if (
                    existing.state
                    == "DELIVERED"
                ):
                    continue

                plans.append(
                    self._plan(
                        event=event,
                        subscription=subscription,
                        record=existing,
                    )
                )
                continue

            record = DeliveryRecord(
                delivery_id=delivery_id,
                event_id=event.event_id,
                subscription_id=(
                    subscription.subscription_id
                ),
                state="PENDING",
                attempt=1,
                max_attempts=(
                    subscription.max_attempts
                ),
            )
            record.validate()

            self._deliveries[
                delivery_id
            ] = record

            plans.append(
                self._plan(
                    event=event,
                    subscription=subscription,
                    record=record,
                )
            )

        return plans

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

    @staticmethod
    def _delivery_id(
        event_id: str,
        subscription_id: str,
    ) -> str:
        material = (
            f"{event_id}\x1f"
            f"{subscription_id}"
        )
        return (
            "delivery_"
            + sha256(
                material.encode("utf-8")
            ).hexdigest()[:24]
        )

    @staticmethod
    def _plan(
        *,
        event: EventEnvelope,
        subscription: Subscription,
        record: DeliveryRecord,
    ) -> DeliveryPlan:
        return DeliveryPlan(
            delivery_id=record.delivery_id,
            event_id=event.event_id,
            subscription_id=(
                subscription.subscription_id
            ),
            target_type=(
                subscription.target_type
            ),
            target_ref=(
                subscription.target_ref
            ),
            attempt=record.attempt,
            tenant_context={
                "organization_id": (
                    event.tenant.organization_id
                ),
                "workspace_id": (
                    event.tenant.workspace_id
                ),
                "project_id": (
                    event.tenant.project_id
                ),
                "environment_id": (
                    event.tenant.environment_id
                ),
            },
            correlation_id=(
                event.correlation_id
            ),
            audit_event={
                "event_type": (
                    "baas.events.delivery_planned"
                ),
                "delivery_id": (
                    record.delivery_id
                ),
                "event_id": (
                    event.event_id
                ),
                "subscription_id": (
                    subscription.subscription_id
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
                "event_id": (
                    event.event_id
                ),
                "subscription_id": (
                    subscription.subscription_id
                ),
                "organization_id": (
                    event.tenant.organization_id
                ),
                "correlation_id": (
                    event.correlation_id
                ),
            },
        )

    def record_success(
        self,
        delivery_id: str,
    ) -> DeliveryRecord:
        record = self._require_delivery(
            delivery_id
        )

        if record.state == "DELIVERED":
            raise EventsBaaSError(
                "delivery already completed"
            )

        if record.state == "DEAD_LETTER":
            raise EventsBaaSError(
                "dead-letter delivery is terminal"
            )

        updated = replace(
            record,
            state="DELIVERED",
            last_error_code=None,
        )

        self._deliveries[
            delivery_id
        ] = updated

        return updated

    def record_failure(
        self,
        *,
        delivery_id: str,
        error_code: str,
    ) -> DeliveryRecord:
        record = self._require_delivery(
            delivery_id
        )

        if record.state in {
            "DELIVERED",
            "DEAD_LETTER",
        }:
            raise EventsBaaSError(
                "terminal delivery cannot fail again"
            )

        code = _text(
            "error_code",
            error_code,
        )

        if record.attempt >= record.max_attempts:
            updated = replace(
                record,
                state="DEAD_LETTER",
                last_error_code=code,
            )
        else:
            updated = replace(
                record,
                state="RETRY_PENDING",
                attempt=(
                    record.attempt + 1
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
    ) -> DeliveryPlan:
        record = self._require_delivery(
            delivery_id
        )

        if record.state != "RETRY_PENDING":
            raise EventsBaaSError(
                "delivery is not retry-pending"
            )

        event = self._events.get(
            record.event_id
        )
        subscription = (
            self._subscriptions.get(
                record.subscription_id
            )
        )

        if (
            event is None
            or subscription is None
        ):
            raise EventsBaaSError(
                "delivery dependencies are missing"
            )

        return self._plan(
            event=event,
            subscription=subscription,
            record=record,
        )

    def _require_delivery(
        self,
        delivery_id: str,
    ) -> DeliveryRecord:
        record = self._deliveries.get(
            str(delivery_id).strip()
        )

        if record is None:
            raise EventsBaaSError(
                "delivery not found"
            )

        return record
