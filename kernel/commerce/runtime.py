from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Any


ENTITY_TYPES = {
    "STORE",
    "BRANCH",
    "PRODUCT",
    "PRODUCT_VARIANT",
    "INVENTORY_ITEM",
    "CUSTOMER",
    "CART",
    "ORDER",
    "ORDER_ITEM",
    "PAYMENT",
    "REFUND",
    "DISCOUNT",
}

CART_STATUSES = {
    "OPEN",
    "CONVERTED",
    "ABANDONED",
}

ORDER_STATUSES = {
    "DRAFT",
    "PLACED",
    "CONFIRMED",
    "COMPLETED",
    "CANCELLED",
}

ORDER_TRANSITIONS = {
    "DRAFT": {"PLACED", "CANCELLED"},
    "PLACED": {"CONFIRMED", "CANCELLED"},
    "CONFIRMED": {"COMPLETED", "CANCELLED"},
    "COMPLETED": set(),
    "CANCELLED": set(),
}

PAYMENT_STATUSES = {
    "PENDING",
    "AUTHORIZED",
    "CAPTURED",
    "FAILED",
    "CANCELLED",
    "REFUNDED",
}

PAYMENT_TRANSITIONS = {
    "PENDING": {"AUTHORIZED", "FAILED", "CANCELLED"},
    "AUTHORIZED": {"CAPTURED", "FAILED", "CANCELLED"},
    "CAPTURED": {"REFUNDED"},
    "FAILED": set(),
    "CANCELLED": set(),
    "REFUNDED": set(),
}

DISCOUNT_TYPES = {
    "FIXED",
    "PERCENTAGE",
}


class CommercePrimitiveError(ValueError):
    pass


def _require_text(name: str, value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise CommercePrimitiveError(
            f"{name} must not be empty"
        )
    return normalized


def validate_currency(currency: str) -> str:
    value = str(currency).strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", value):
        raise CommercePrimitiveError(
            "currency must be three uppercase letters"
        )
    return value


@dataclass(frozen=True)
class Money:
    amount_minor: int
    currency: str

    def validate(self, *, allow_negative: bool = False) -> None:
        if not isinstance(self.amount_minor, int):
            raise CommercePrimitiveError(
                "amount_minor must be an integer"
            )
        if not allow_negative and self.amount_minor < 0:
            raise CommercePrimitiveError(
                "amount_minor must be >= 0"
            )
        validate_currency(self.currency)


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
            _require_text(name, value)


@dataclass(frozen=True)
class CommerceResource:
    id: str
    entity_type: str
    tenant: TenantScope
    created_at: str
    updated_at: str

    def validate(self) -> None:
        _require_text("id", self.id)

        if self.entity_type not in ENTITY_TYPES:
            raise CommercePrimitiveError(
                f"unsupported entity_type: {self.entity_type}"
            )

        self.tenant.validate()

        for name, value in {
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }.items():
            try:
                datetime.fromisoformat(value)
            except ValueError as exc:
                raise CommercePrimitiveError(
                    f"{name} must be ISO-8601"
                ) from exc


@dataclass(frozen=True)
class ProductVariant:
    resource: CommerceResource
    product_id: str
    sku: str
    price: Money
    active: bool = True

    def validate(self) -> None:
        self.resource.validate()

        if self.resource.entity_type != "PRODUCT_VARIANT":
            raise CommercePrimitiveError(
                "resource entity_type must be PRODUCT_VARIANT"
            )

        _require_text("product_id", self.product_id)
        _require_text("sku", self.sku)
        self.price.validate()


@dataclass(frozen=True)
class InventoryItem:
    resource: CommerceResource
    product_variant_id: str
    store_id: str
    branch_id: str | None
    quantity_on_hand: int
    quantity_reserved: int = 0

    def validate(self) -> None:
        self.resource.validate()

        if self.resource.entity_type != "INVENTORY_ITEM":
            raise CommercePrimitiveError(
                "resource entity_type must be INVENTORY_ITEM"
            )

        _require_text(
            "product_variant_id",
            self.product_variant_id,
        )
        _require_text("store_id", self.store_id)

        if not isinstance(self.quantity_on_hand, int):
            raise CommercePrimitiveError(
                "quantity_on_hand must be an integer"
            )

        if not isinstance(self.quantity_reserved, int):
            raise CommercePrimitiveError(
                "quantity_reserved must be an integer"
            )

        if self.quantity_on_hand < 0:
            raise CommercePrimitiveError(
                "quantity_on_hand may not be negative"
            )

        if self.quantity_reserved < 0:
            raise CommercePrimitiveError(
                "quantity_reserved may not be negative"
            )

        if self.quantity_reserved > self.quantity_on_hand:
            raise CommercePrimitiveError(
                "quantity_reserved may not exceed quantity_on_hand"
            )

    @property
    def quantity_available(self) -> int:
        self.validate()
        return self.quantity_on_hand - self.quantity_reserved


@dataclass(frozen=True)
class OrderState:
    order_id: str
    status: str

    def validate(self) -> None:
        _require_text("order_id", self.order_id)
        if self.status not in ORDER_STATUSES:
            raise CommercePrimitiveError(
                f"invalid order status: {self.status}"
            )

    def transition(self, target: str) -> "OrderState":
        self.validate()
        target = str(target).strip().upper()

        if target not in ORDER_STATUSES:
            raise CommercePrimitiveError(
                f"invalid target order status: {target}"
            )

        if target not in ORDER_TRANSITIONS[self.status]:
            raise CommercePrimitiveError(
                f"illegal order transition: {self.status} -> {target}"
            )

        return OrderState(
            order_id=self.order_id,
            status=target,
        )


@dataclass(frozen=True)
class PaymentState:
    payment_id: str
    order_id: str
    status: str
    amount: Money

    def validate(self) -> None:
        _require_text("payment_id", self.payment_id)
        _require_text("order_id", self.order_id)

        if self.status not in PAYMENT_STATUSES:
            raise CommercePrimitiveError(
                f"invalid payment status: {self.status}"
            )

        self.amount.validate()

    def transition(self, target: str) -> "PaymentState":
        self.validate()
        target = str(target).strip().upper()

        if target not in PAYMENT_STATUSES:
            raise CommercePrimitiveError(
                f"invalid target payment status: {target}"
            )

        if target not in PAYMENT_TRANSITIONS[self.status]:
            raise CommercePrimitiveError(
                f"illegal payment transition: {self.status} -> {target}"
            )

        return PaymentState(
            payment_id=self.payment_id,
            order_id=self.order_id,
            status=target,
            amount=self.amount,
        )


@dataclass(frozen=True)
class Refund:
    refund_id: str
    payment_id: str
    amount: Money
    reason: str

    def validate(
        self,
        *,
        captured_amount: Money,
        previously_refunded_minor: int = 0,
    ) -> None:
        _require_text("refund_id", self.refund_id)
        _require_text("payment_id", self.payment_id)
        _require_text("reason", self.reason)

        self.amount.validate()
        captured_amount.validate()

        if (
            validate_currency(self.amount.currency)
            != validate_currency(captured_amount.currency)
        ):
            raise CommercePrimitiveError(
                "refund currency must match captured payment currency"
            )

        if not isinstance(previously_refunded_minor, int):
            raise CommercePrimitiveError(
                "previously_refunded_minor must be an integer"
            )

        if previously_refunded_minor < 0:
            raise CommercePrimitiveError(
                "previously_refunded_minor must be >= 0"
            )

        total = (
            previously_refunded_minor
            + self.amount.amount_minor
        )

        if total > captured_amount.amount_minor:
            raise CommercePrimitiveError(
                "refund total may not exceed captured payment amount"
            )


@dataclass(frozen=True)
class Discount:
    discount_id: str
    discount_type: str
    value_minor: int | None = None
    basis_points: int | None = None
    currency: str | None = None

    def validate(self) -> None:
        _require_text("discount_id", self.discount_id)

        if self.discount_type not in DISCOUNT_TYPES:
            raise CommercePrimitiveError(
                f"invalid discount_type: {self.discount_type}"
            )

        if self.discount_type == "FIXED":
            if (
                not isinstance(self.value_minor, int)
                or self.value_minor <= 0
            ):
                raise CommercePrimitiveError(
                    "FIXED discount requires value_minor > 0"
                )

            if self.basis_points is not None:
                raise CommercePrimitiveError(
                    "FIXED discount may not define basis_points"
                )

            if self.currency is None:
                raise CommercePrimitiveError(
                    "FIXED discount requires currency"
                )

            validate_currency(self.currency)

        if self.discount_type == "PERCENTAGE":
            if (
                not isinstance(self.basis_points, int)
                or self.basis_points < 1
                or self.basis_points > 10000
            ):
                raise CommercePrimitiveError(
                    "PERCENTAGE discount requires basis_points 1..10000"
                )

            if self.value_minor is not None:
                raise CommercePrimitiveError(
                    "PERCENTAGE discount may not define value_minor"
                )


def validate_cart_transition(
    current: str,
    target: str,
) -> str:
    current = str(current).strip().upper()
    target = str(target).strip().upper()

    if current not in CART_STATUSES:
        raise CommercePrimitiveError(
            f"invalid cart status: {current}"
        )

    if target not in CART_STATUSES:
        raise CommercePrimitiveError(
            f"invalid target cart status: {target}"
        )

    if current != "OPEN":
        raise CommercePrimitiveError(
            f"cart status is terminal: {current}"
        )

    if target not in {"CONVERTED", "ABANDONED"}:
        raise CommercePrimitiveError(
            f"illegal cart transition: {current} -> {target}"
        )

    return target
