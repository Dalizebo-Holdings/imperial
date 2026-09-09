from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4
import json
import asyncio
import weakref

from baas.runtime.request_context import BaaSRequestContext


class RealtimeBaaSError(ValueError):
    pass


class SubscriptionKind(str, Enum):
    DATABASE_CHANGES = "database.changes"
    INVENTORY_UPDATES = "inventory.updates"
    ORDER_UPDATES = "order.updates"
    PRESENCE = "presence"
    APPLICATION_EVENTS = "application.events"


class SubscriptionFilterOperator(str, Enum):
    EQUALS = "eq"
    NOT_EQUALS = "neq"
    IN = "in"
    NOT_IN = "nin"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    LIKE = "like"
    ILIKE = "ilike"


@dataclass(frozen=True, slots=True)
class SubscriptionFilter:
    field: str
    operator: SubscriptionFilterOperator
    value: Any

    def validate(self) -> None:
        if not self.field.strip():
            raise RealtimeBaaSError("filter field must not be empty")
        if not isinstance(self.operator, SubscriptionFilterOperator):
            raise RealtimeBaaSError("invalid filter operator")


@dataclass(frozen=True, slots=True)
class RealtimeSubscription:
    subscription_id: str
    tenant_id: str
    kind: SubscriptionKind
    resource_type: str | None
    filters: tuple[SubscriptionFilter, ...]
    cursor: str | None
    created_at: datetime
    acknowledged: bool = False


@dataclass(frozen=True, slots=True)
class RealtimeEvent:
    event_id: str
    subscription_id: str
    kind: SubscriptionKind
    resource_type: str
    resource_id: str
    action: str
    payload: dict[str, Any]
    tenant_id: str
    correlation_id: str | None
    occurred_at: datetime
    cursor: str


@dataclass(frozen=True, slots=True)
class RealtimeAcknowledgement:
    event_id: str
    subscription_id: str
    acknowledged_at: datetime


class RealtimeConnection:
    def __init__(self, connection_id: str, subscription: RealtimeSubscription) -> None:
        self.connection_id = connection_id
        self.subscription = subscription
        self._queue: asyncio.Queue[RealtimeEvent] = asyncio.Queue()
        self._closed = False
        self._last_ack_cursor: str | None = None

    async def send(self, event: RealtimeEvent) -> None:
        if self._closed:
            raise RealtimeBaaSError("connection is closed")
        await self._queue.put(event)

    async def receive(self) -> RealtimeEvent | None:
        if self._closed:
            return None
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=30.0)
        except asyncio.TimeoutError:
            return None

    def acknowledge(self, event_id: str, cursor: str) -> None:
        self._last_ack_cursor = cursor

    def close(self) -> None:
        self._closed = True


class RealtimeManager:
    def __init__(self) -> None:
        self._subscriptions: dict[str, RealtimeSubscription] = {}
        self._connections: dict[str, RealtimeConnection] = {}
        self._tenant_subscriptions: dict[str, set[str]] = {}
        self._event_cursor = 0

    def _validate_request_context(self, ctx: BaaSRequestContext) -> None:
        ctx.validate()
        if not str(ctx.kernel_authorization_ref).startswith("kernel_auth_"):
            raise RealtimeBaaSError("realtime operations require Kernel authorization evidence")

    def _get_tenant_id(self, ctx: BaaSRequestContext) -> str:
        return f"{ctx.organization_id}/{ctx.workspace_id}/{ctx.project_id}/{ctx.environment_id}"

    def create_subscription(
        self,
        *,
        kind: SubscriptionKind,
        resource_type: str | None,
        filters: tuple[SubscriptionFilter, ...] = (),
        cursor: str | None,
        ctx: BaaSRequestContext,
    ) -> RealtimeSubscription:
        self._validate_request_context(ctx)
        tenant_id = self._get_tenant_id(ctx)

        for f in filters:
            f.validate()

        subscription_id = f"rts_{uuid4().hex[:24]}"
        subscription = RealtimeSubscription(
            subscription_id=subscription_id,
            tenant_id=tenant_id,
            kind=kind,
            resource_type=resource_type,
            filters=filters,
            cursor=cursor,
            created_at=datetime.now(timezone.utc),
        )

        self._subscriptions[subscription_id] = subscription
        if tenant_id not in self._tenant_subscriptions:
            self._tenant_subscriptions[tenant_id] = set()
        self._tenant_subscriptions[tenant_id].add(subscription_id)

        return subscription

    def delete_subscription(
        self,
        *,
        subscription_id: str,
        ctx: BaaSRequestContext,
    ) -> None:
        self._validate_request_context(ctx)
        tenant_id = self._get_tenant_id(ctx)

        subscription = self._subscriptions.get(subscription_id)
        if not subscription:
            raise RealtimeBaaSError("subscription not found")
        if subscription.tenant_id != tenant_id:
            raise RealtimeBaaSError("cross-tenant subscription access denied")

        del self._subscriptions[subscription_id]
        self._tenant_subscriptions[tenant_id].discard(subscription_id)

        for conn_id, conn in list(self._connections.items()):
            if conn.subscription.subscription_id == subscription_id:
                conn.close()
                del self._connections[conn_id]

    def connect(
        self,
        *,
        subscription_id: str,
        ctx: BaaSRequestContext,
    ) -> RealtimeConnection:
        self._validate_request_context(ctx)
        tenant_id = self._get_tenant_id(ctx)

        subscription = self._subscriptions.get(subscription_id)
        if not subscription:
            raise RealtimeBaaSError("subscription not found")
        if subscription.tenant_id != tenant_id:
            raise RealtimeBaaSError("cross-tenant subscription access denied")

        if subscription_id in {c.subscription.subscription_id for c in self._connections.values()}:
            raise RealtimeBaaSError("subscription already has an active connection")

        connection_id = f"rtc_{uuid4().hex[:24]}"
        connection = RealtimeConnection(connection_id, subscription)
        self._connections[connection_id] = connection

        return connection

    def disconnect(
        self,
        *,
        connection_id: str,
        ctx: BaaSRequestContext,
    ) -> None:
        self._validate_request_context(ctx)

        connection = self._connections.get(connection_id)
        if not connection:
            return

        tenant_id = self._get_tenant_id(ctx)
        if connection.subscription.tenant_id != tenant_id:
            raise RealtimeBaaSError("cross-tenant connection access denied")

        connection.close()
        del self._connections[connection_id]

    def broadcast(
        self,
        *,
        kind: SubscriptionKind,
        resource_type: str,
        resource_id: str,
        action: str,
        payload: dict[str, Any],
        tenant_id: str,
        correlation_id: str | None = None,
    ) -> int:
        if tenant_id not in self._tenant_subscriptions:
            return 0

        self._event_cursor += 1
        cursor = f"{self._event_cursor:020d}"
        occurred_at = datetime.now(timezone.utc)

        event = RealtimeEvent(
            event_id=f"rte_{uuid4().hex[:24]}",
            subscription_id="",
            kind=kind,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            payload=payload,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            occurred_at=occurred_at,
            cursor=cursor,
        )

        delivered = 0
        for sub_id in self._tenant_subscriptions[tenant_id]:
            subscription = self._subscriptions.get(sub_id)
            if not subscription or subscription.kind != kind:
                continue

            if subscription.resource_type and subscription.resource_type != resource_type:
                continue

            if not self._matches_filters(subscription.filters, payload):
                continue

            if subscription.cursor and subscription.cursor >= cursor:
                continue

            for conn in self._connections.values():
                if conn.subscription.subscription_id == sub_id:
                    updated_event = RealtimeEvent(
                        event_id=event.event_id,
                        subscription_id=sub_id,
                        kind=event.kind,
                        resource_type=event.resource_type,
                        resource_id=event.resource_id,
                        action=event.action,
                        payload=event.payload,
                        tenant_id=event.tenant_id,
                        correlation_id=event.correlation_id,
                        occurred_at=event.occurred_at,
                        cursor=event.cursor,
                    )
                    try:
                        conn._queue.put_nowait(updated_event)
                        delivered += 1
                    except Exception:
                        pass

        return delivered

    def _matches_filters(
        self,
        filters: tuple[SubscriptionFilter, ...],
        payload: dict[str, Any],
    ) -> bool:
        for f in filters:
            field_value = payload.get(f.field)
            if field_value is None:
                return False

            match f.operator:
                case SubscriptionFilterOperator.EQUALS:
                    if field_value != f.value:
                        return False
                case SubscriptionFilterOperator.NOT_EQUALS:
                    if field_value == f.value:
                        return False
                case SubscriptionFilterOperator.IN:
                    if field_value not in f.value:
                        return False
                case SubscriptionFilterOperator.NOT_IN:
                    if field_value in f.value:
                        return False
                case SubscriptionFilterOperator.GREATER_THAN:
                    if not (field_value > f.value):
                        return False
                case SubscriptionFilterOperator.GREATER_THAN_OR_EQUAL:
                    if not (field_value >= f.value):
                        return False
                case SubscriptionFilterOperator.LESS_THAN:
                    if not (field_value < f.value):
                        return False
                case SubscriptionFilterOperator.LESS_THAN_OR_EQUAL:
                    if not (field_value <= f.value):
                        return False
                case SubscriptionFilterOperator.LIKE:
                    if not isinstance(field_value, str) or not isinstance(f.value, str):
                        return False
                    if f.value not in field_value:
                        return False
                case SubscriptionFilterOperator.ILIKE:
                    if not isinstance(field_value, str) or not isinstance(f.value, str):
                        return False
                    if f.value.lower() not in field_value.lower():
                        return False

        return True

    def get_subscription(self, subscription_id: str, ctx: BaaSRequestContext) -> RealtimeSubscription:
        self._validate_request_context(ctx)
        tenant_id = self._get_tenant_id(ctx)

        subscription = self._subscriptions.get(subscription_id)
        if not subscription or subscription.tenant_id != tenant_id:
            raise RealtimeBaaSError("cross-tenant subscription access denied")
        return subscription

    def list_subscriptions(self, ctx: BaaSRequestContext) -> list[RealtimeSubscription]:
        self._validate_request_context(ctx)
        tenant_id = self._get_tenant_id(ctx)

        return [
            s for s in self._subscriptions.values()
            if s.tenant_id == tenant_id
        ]

    def get_connection_stats(self, ctx: BaaSRequestContext) -> dict[str, Any]:
        self._validate_request_context(ctx)
        tenant_id = self._get_tenant_id(ctx)

        tenant_connections = [
            c for c in self._connections.values()
            if c.subscription.tenant_id == tenant_id
        ]

        return {
            "active_connections": len(tenant_connections),
            "total_subscriptions": len(self._tenant_subscriptions.get(tenant_id, set())),
            "connection_ids": [c.connection_id for c in tenant_connections],
        }