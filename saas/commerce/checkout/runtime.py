from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any


class CommerceCheckoutError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise CommerceCheckoutError(
            f"{name} must not be empty"
        )
    result = str(value).strip()
    if not result:
        raise CommerceCheckoutError(
            f"{name} must not be empty"
        )
    return result


def _time(value: str | None = None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CommerceCheckoutError(
            "timestamp must be ISO-8601"
        ) from exc
    if parsed.tzinfo is None:
        raise CommerceCheckoutError(
            "timestamp must be timezone-aware"
        )
    return parsed.isoformat()


def _canonical(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except (TypeError, ValueError) as exc:
        raise CommerceCheckoutError(
            "checkout material must be JSON-compatible"
        ) from exc


def _validate_context(context: Any) -> None:
    if hasattr(context, "validate"):
        context.validate()

    if (
        str(getattr(context, "product", "")).strip().upper()
        != "COMMERCE"
    ):
        raise CommerceCheckoutError(
            "Commerce Cart/Checkout requires product=COMMERCE"
        )

    if getattr(context, "store_id", None) is None:
        raise CommerceCheckoutError(
            "Commerce Cart/Checkout requires store context"
        )


@dataclass(frozen=True)
class CommerceEvidence:
    source: str
    entity_type: str
    entity_id: str
    organization_id: str
    workspace_id: str
    project_id: str
    environment_id: str
    snapshot_ref: str

    def validate(self) -> None:
        if str(self.source).strip() != "kernel.commerce":
            raise CommerceCheckoutError(
                "evidence must come from kernel.commerce"
            )

        for name, value in {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "environment_id": self.environment_id,
            "snapshot_ref": self.snapshot_ref,
        }.items():
            _text(name, value)


@dataclass(frozen=True)
class CheckoutLineSnapshot:
    order_item_id: str
    product_id: str
    product_variant_id: str
    inventory_item_id: str
    quantity: int
    unit_price_minor: int
    currency: str
    expected_quantity_on_hand: int
    expected_quantity_reserved: int
    product_evidence: CommerceEvidence
    variant_evidence: CommerceEvidence
    inventory_evidence: CommerceEvidence

    def validate_basic(self) -> None:
        for name, value in {
            "order_item_id": self.order_item_id,
            "product_id": self.product_id,
            "product_variant_id": self.product_variant_id,
            "inventory_item_id": self.inventory_item_id,
        }.items():
            _text(name, value)

        if (
            not isinstance(self.quantity, int)
            or isinstance(self.quantity, bool)
            or self.quantity <= 0
        ):
            raise CommerceCheckoutError(
                "checkout line quantity must be an integer > 0"
            )

        if (
            not isinstance(self.unit_price_minor, int)
            or isinstance(self.unit_price_minor, bool)
            or self.unit_price_minor < 0
        ):
            raise CommerceCheckoutError(
                "unit_price_minor must be an integer >= 0"
            )

        for name, value in {
            "expected_quantity_on_hand": self.expected_quantity_on_hand,
            "expected_quantity_reserved": self.expected_quantity_reserved,
        }.items():
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 0
            ):
                raise CommerceCheckoutError(
                    f"{name} must be an integer >= 0"
                )


@dataclass(frozen=True)
class CartCreateRequest:
    cart_id: str
    store_id: str
    customer_id: str | None
    currency: str
    idempotency_key: str
    requested_at: str

    def validate(self) -> None:
        for name, value in {
            "cart_id": self.cart_id,
            "store_id": self.store_id,
            "currency": self.currency,
            "idempotency_key": self.idempotency_key,
        }.items():
            _text(name, value)
        _time(self.requested_at)


@dataclass(frozen=True)
class CheckoutRequest:
    checkout_id: str
    cart_id: str
    order_id: str
    store_id: str
    customer_id: str | None
    currency: str
    lines: tuple[CheckoutLineSnapshot, ...]
    idempotency_key: str
    requested_at: str

    def validate_basic(self) -> None:
        for name, value in {
            "checkout_id": self.checkout_id,
            "cart_id": self.cart_id,
            "order_id": self.order_id,
            "store_id": self.store_id,
            "currency": self.currency,
            "idempotency_key": self.idempotency_key,
        }.items():
            _text(name, value)

        if not self.lines:
            raise CommerceCheckoutError(
                "checkout requires at least one line"
            )

        ids = set()
        for line in self.lines:
            line.validate_basic()
            if line.order_item_id in ids:
                raise CommerceCheckoutError(
                    "duplicate order_item_id"
                )
            ids.add(line.order_item_id)

        _time(self.requested_at)


@dataclass(frozen=True)
class CheckoutTransactionPlan:
    checkout_id: str
    transaction_id: str
    cart_id: str
    order_id: str
    subtotal_minor: int
    discount_minor: int
    tax_minor: int
    total_minor: int
    currency: str
    inventory_reservations: tuple[Any, ...]
    order_create: Any
    order_items: tuple[Any, ...]
    cart_transition: Any
    order_transition: Any
    correlation_id: str
    kernel_authorization_ref: str
    transaction_requirement: str = "KERNEL_ATOMIC_TRANSACTION"
    event_publication: str = "OUTBOX_AFTER_COMMIT"
    failure_policy: str = "ROLLBACK_ALL_MUTATIONS"
    state: str = "READY_FOR_KERNEL_TRANSACTION_ADAPTER"


class CommerceCartCheckoutOrdersService:
    def __init__(
        self,
        *,
        foundation: Any,
        product_command_type: Any,
        kernel_tenant_scope_type: Any,
        kernel_resource_type: Any,
        kernel_inventory_type: Any,
        kernel_money_type: Any,
        kernel_order_state_type: Any,
        kernel_cart_transition: Any,
        kernel_currency_validator: Any,
    ) -> None:
        self._foundation = foundation
        self._product_command_type = product_command_type
        self._kernel_tenant_scope_type = kernel_tenant_scope_type
        self._kernel_resource_type = kernel_resource_type
        self._kernel_inventory_type = kernel_inventory_type
        self._kernel_money_type = kernel_money_type
        self._kernel_order_state_type = kernel_order_state_type
        self._kernel_cart_transition = kernel_cart_transition
        self._kernel_currency_validator = kernel_currency_validator
        self._checkout_idempotency: dict[
            tuple[str, str, str],
            tuple[str, str],
        ] = {}

    @staticmethod
    def _assert_evidence(
        *,
        context: Any,
        evidence: CommerceEvidence,
        entity_type: str,
        entity_id: str,
    ) -> None:
        evidence.validate()

        if str(evidence.entity_type).strip().upper() != entity_type:
            raise CommerceCheckoutError(
                "evidence entity_type mismatch"
            )

        if evidence.entity_id != entity_id:
            raise CommerceCheckoutError(
                "evidence entity_id mismatch"
            )

        for name in [
            "organization_id",
            "workspace_id",
            "project_id",
            "environment_id",
        ]:
            if getattr(evidence, name) != getattr(context, name):
                raise CommerceCheckoutError(
                    "evidence tenant scope mismatch"
                )

    def _tenant(self, context: Any) -> Any:
        tenant = self._kernel_tenant_scope_type(
            organization_id=context.organization_id,
            workspace_id=context.workspace_id,
            project_id=context.project_id,
            environment_id=context.environment_id,
        )
        tenant.validate()
        return tenant

    def _validate_inventory_target(
        self,
        *,
        context: Any,
        line: CheckoutLineSnapshot,
        store_id: str,
        timestamp: str,
    ) -> tuple[int, int]:
        target_on_hand = line.expected_quantity_on_hand
        target_reserved = (
            line.expected_quantity_reserved
            + line.quantity
        )

        resource = self._kernel_resource_type(
            id=line.inventory_item_id,
            entity_type="INVENTORY_ITEM",
            tenant=self._tenant(context),
            created_at=timestamp,
            updated_at=timestamp,
        )

        item = self._kernel_inventory_type(
            resource=resource,
            product_variant_id=line.product_variant_id,
            store_id=store_id,
            branch_id=None,
            quantity_on_hand=target_on_hand,
            quantity_reserved=target_reserved,
        )

        try:
            item.validate()
        except Exception as exc:
            raise CommerceCheckoutError(
                "checkout inventory reservation violates Kernel invariants"
            ) from exc

        return target_on_hand, target_reserved

    def plan_cart_create(
        self,
        *,
        context: Any,
        request: CartCreateRequest,
        store_evidence: CommerceEvidence,
        customer_evidence: CommerceEvidence | None = None,
    ) -> dict[str, Any]:
        _validate_context(context)
        request.validate()

        if context.store_id != request.store_id:
            raise CommerceCheckoutError(
                "Cart store_id must match Commerce context"
            )

        self._assert_evidence(
            context=context,
            evidence=store_evidence,
            entity_type="STORE",
            entity_id=request.store_id,
        )

        if request.customer_id is not None:
            if customer_evidence is None:
                raise CommerceCheckoutError(
                    "customer evidence is required"
                )
            self._assert_evidence(
                context=context,
                evidence=customer_evidence,
                entity_type="CUSTOMER",
                entity_id=request.customer_id,
            )

        currency = self._kernel_currency_validator(
            request.currency
        )

        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="CART",
                entity_id=request.cart_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    "store_id": request.store_id,
                    "customer_id": request.customer_id,
                    "status": "OPEN",
                    "currency": currency,
                    "requested_at": _time(request.requested_at),
                    "cart_line_persistence": (
                        "DEFERRED_SHARED_KERNEL_CART_ITEM_PRIMITIVE"
                    ),
                },
            )
        )

    def plan_cart_abandon(
        self,
        *,
        context: Any,
        cart_evidence: CommerceEvidence,
        idempotency_key: str,
        requested_at: str,
    ) -> dict[str, Any]:
        _validate_context(context)

        self._assert_evidence(
            context=context,
            evidence=cart_evidence,
            entity_type="CART",
            entity_id=cart_evidence.entity_id,
        )

        try:
            target = self._kernel_cart_transition(
                "OPEN",
                "ABANDONED",
            )
        except Exception as exc:
            raise CommerceCheckoutError(
                "Kernel rejected Cart abandonment"
            ) from exc

        return self._foundation.plan(
            self._product_command_type(
                action="TRANSITION",
                entity_type="CART",
                entity_id=cart_evidence.entity_id,
                context=context,
                idempotency_key=_text(
                    "idempotency_key",
                    idempotency_key,
                ),
                input_metadata={
                    "from_status": "OPEN",
                    "to_status": target,
                    "requested_at": _time(requested_at),
                },
            )
        )

    def plan_checkout(
        self,
        *,
        context: Any,
        request: CheckoutRequest,
        store_evidence: CommerceEvidence,
        cart_evidence: CommerceEvidence,
        customer_evidence: CommerceEvidence | None = None,
    ) -> dict[str, Any]:
        _validate_context(context)
        request.validate_basic()

        if context.store_id != request.store_id:
            raise CommerceCheckoutError(
                "Checkout store_id must match Commerce context"
            )

        self._assert_evidence(
            context=context,
            evidence=store_evidence,
            entity_type="STORE",
            entity_id=request.store_id,
        )
        self._assert_evidence(
            context=context,
            evidence=cart_evidence,
            entity_type="CART",
            entity_id=request.cart_id,
        )

        if request.customer_id is not None:
            if customer_evidence is None:
                raise CommerceCheckoutError(
                    "checkout customer evidence is required"
                )
            self._assert_evidence(
                context=context,
                evidence=customer_evidence,
                entity_type="CUSTOMER",
                entity_id=request.customer_id,
            )

        currency = self._kernel_currency_validator(
            request.currency
        )
        timestamp = _time(request.requested_at)

        line_material = []
        subtotal_minor = 0

        for line in request.lines:
            self._assert_evidence(
                context=context,
                evidence=line.product_evidence,
                entity_type="PRODUCT",
                entity_id=line.product_id,
            )
            self._assert_evidence(
                context=context,
                evidence=line.variant_evidence,
                entity_type="PRODUCT_VARIANT",
                entity_id=line.product_variant_id,
            )
            self._assert_evidence(
                context=context,
                evidence=line.inventory_evidence,
                entity_type="INVENTORY_ITEM",
                entity_id=line.inventory_item_id,
            )

            line_currency = self._kernel_currency_validator(
                line.currency
            )
            if line_currency != currency:
                raise CommerceCheckoutError(
                    "all checkout lines must use checkout currency"
                )

            money = self._kernel_money_type(
                amount_minor=line.unit_price_minor,
                currency=line_currency,
            )
            try:
                money.validate()
            except Exception as exc:
                raise CommerceCheckoutError(
                    "Kernel rejected checkout line price"
                ) from exc

            line_total = line.quantity * line.unit_price_minor
            subtotal_minor += line_total

            line_material.append(
                {
                    "order_item_id": line.order_item_id,
                    "product_id": line.product_id,
                    "product_variant_id": line.product_variant_id,
                    "inventory_item_id": line.inventory_item_id,
                    "quantity": line.quantity,
                    "unit_price_minor": line.unit_price_minor,
                    "total_minor": line_total,
                    "currency": line_currency,
                    "expected_quantity_on_hand": (
                        line.expected_quantity_on_hand
                    ),
                    "expected_quantity_reserved": (
                        line.expected_quantity_reserved
                    ),
                    "product_snapshot_ref": (
                        line.product_evidence.snapshot_ref
                    ),
                    "variant_snapshot_ref": (
                        line.variant_evidence.snapshot_ref
                    ),
                    "inventory_snapshot_ref": (
                        line.inventory_evidence.snapshot_ref
                    ),
                }
            )

        canonical_request = {
            "checkout_id": request.checkout_id,
            "cart_id": request.cart_id,
            "order_id": request.order_id,
            "store_id": request.store_id,
            "customer_id": request.customer_id,
            "currency": currency,
            "lines": line_material,
        }

        request_hash = sha256(
            _canonical(canonical_request).encode("utf-8")
        ).hexdigest()

        idem_scope = (
            context.organization_id,
            context.environment_id,
            request.idempotency_key,
        )

        existing = self._checkout_idempotency.get(
            idem_scope
        )
        if existing is not None:
            existing_hash, transaction_id = existing
            if existing_hash != request_hash:
                raise CommerceCheckoutError(
                    "checkout idempotency key reused with different request"
                )
        else:
            transaction_id = (
                "checkout_tx_"
                + sha256(
                    _canonical(
                        {
                            "scope": idem_scope,
                            "request_hash": request_hash,
                        }
                    ).encode("utf-8")
                ).hexdigest()[:24]
            )
            self._checkout_idempotency[
                idem_scope
            ] = (
                request_hash,
                transaction_id,
            )

        inventory_plans = []
        order_item_plans = []

        for line in request.lines:
            target_on_hand, target_reserved = (
                self._validate_inventory_target(
                    context=context,
                    line=line,
                    store_id=request.store_id,
                    timestamp=timestamp,
                )
            )

            inventory_plans.append(
                self._foundation.plan(
                    self._product_command_type(
                        action="UPDATE",
                        entity_type="INVENTORY_ITEM",
                        entity_id=line.inventory_item_id,
                        context=context,
                        idempotency_key=(
                            f"{request.idempotency_key}:reserve:{line.inventory_item_id}"
                        ),
                        input_metadata={
                            "expected_quantity_on_hand": (
                                line.expected_quantity_on_hand
                            ),
                            "expected_quantity_reserved": (
                                line.expected_quantity_reserved
                            ),
                            "target_quantity_on_hand": target_on_hand,
                            "target_quantity_reserved": target_reserved,
                            "quantity_reserved_delta": line.quantity,
                            "reason": "CHECKOUT_RESERVATION",
                            "source_ref": (
                                f"checkout://{request.checkout_id}"
                            ),
                            "persistence_requirement": (
                                "ATOMIC_COMPARE_EXPECTED_AND_UPDATE"
                            ),
                            "requested_at": timestamp,
                        },
                    )
                )["plan"]
            )

            order_item_plans.append(
                self._foundation.plan(
                    self._product_command_type(
                        action="CREATE",
                        entity_type="ORDER_ITEM",
                        entity_id=line.order_item_id,
                        context=context,
                        idempotency_key=(
                            f"{request.idempotency_key}:order-item:{line.order_item_id}"
                        ),
                        input_metadata={
                            "order_id": request.order_id,
                            "product_id": line.product_id,
                            "product_variant_id": line.product_variant_id,
                            "quantity": line.quantity,
                            "unit_price_minor": line.unit_price_minor,
                            "total_minor": (
                                line.quantity
                                * line.unit_price_minor
                            ),
                            "currency": currency,
                            "pricing_snapshot_ref": (
                                line.variant_evidence.snapshot_ref
                            ),
                            "requested_at": timestamp,
                        },
                    )
                )["plan"]
            )

        order_create = self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="ORDER",
                entity_id=request.order_id,
                context=context,
                idempotency_key=(
                    f"{request.idempotency_key}:order"
                ),
                input_metadata={
                    "store_id": request.store_id,
                    "branch_id": None,
                    "customer_id": request.customer_id,
                    "cart_id": request.cart_id,
                    "status": "DRAFT",
                    "currency": currency,
                    "subtotal_minor": subtotal_minor,
                    "discount_minor": 0,
                    "tax_minor": 0,
                    "total_minor": subtotal_minor,
                    "requested_at": timestamp,
                },
            )
        )["plan"]

        try:
            cart_target = self._kernel_cart_transition(
                "OPEN",
                "CONVERTED",
            )
        except Exception as exc:
            raise CommerceCheckoutError(
                "Kernel rejected Cart conversion"
            ) from exc

        cart_transition = self._foundation.plan(
            self._product_command_type(
                action="TRANSITION",
                entity_type="CART",
                entity_id=request.cart_id,
                context=context,
                idempotency_key=(
                    f"{request.idempotency_key}:cart-convert"
                ),
                input_metadata={
                    "from_status": "OPEN",
                    "to_status": cart_target,
                    "checkout_id": request.checkout_id,
                    "order_id": request.order_id,
                    "requested_at": timestamp,
                },
            )
        )["plan"]

        try:
            placed = self._kernel_order_state_type(
                order_id=request.order_id,
                status="DRAFT",
            ).transition("PLACED")
        except Exception as exc:
            raise CommerceCheckoutError(
                "Kernel rejected Order placement"
            ) from exc

        order_transition = self._foundation.plan(
            self._product_command_type(
                action="TRANSITION",
                entity_type="ORDER",
                entity_id=request.order_id,
                context=context,
                idempotency_key=(
                    f"{request.idempotency_key}:order-place"
                ),
                input_metadata={
                    "from_status": "DRAFT",
                    "to_status": placed.status,
                    "checkout_id": request.checkout_id,
                    "requested_at": timestamp,
                },
            )
        )["plan"]

        plan = CheckoutTransactionPlan(
            checkout_id=request.checkout_id,
            transaction_id=transaction_id,
            cart_id=request.cart_id,
            order_id=request.order_id,
            subtotal_minor=subtotal_minor,
            discount_minor=0,
            tax_minor=0,
            total_minor=subtotal_minor,
            currency=currency,
            inventory_reservations=tuple(
                inventory_plans
            ),
            order_create=order_create,
            order_items=tuple(
                order_item_plans
            ),
            cart_transition=cart_transition,
            order_transition=order_transition,
            correlation_id=context.correlation_id,
            kernel_authorization_ref=(
                context.kernel_authorization_ref
            ),
        )

        return {
            "created": existing is None,
            "plan": plan,
        }

    def plan_order_transition(
        self,
        *,
        context: Any,
        order_evidence: CommerceEvidence,
        current_status: str,
        target_status: str,
        idempotency_key: str,
        requested_at: str,
    ) -> dict[str, Any]:
        _validate_context(context)

        self._assert_evidence(
            context=context,
            evidence=order_evidence,
            entity_type="ORDER",
            entity_id=order_evidence.entity_id,
        )

        try:
            state = self._kernel_order_state_type(
                order_id=order_evidence.entity_id,
                status=str(current_status).strip().upper(),
            )
            target = state.transition(
                str(target_status).strip().upper()
            )
        except Exception as exc:
            raise CommerceCheckoutError(
                "Kernel rejected Order lifecycle transition"
            ) from exc

        return self._foundation.plan(
            self._product_command_type(
                action="TRANSITION",
                entity_type="ORDER",
                entity_id=order_evidence.entity_id,
                context=context,
                idempotency_key=_text(
                    "idempotency_key",
                    idempotency_key,
                ),
                input_metadata={
                    "from_status": state.status,
                    "to_status": target.status,
                    "requested_at": _time(requested_at),
                },
            )
        )
