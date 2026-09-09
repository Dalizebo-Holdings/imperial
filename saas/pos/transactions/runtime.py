from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any


class POSTransactionError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise POSTransactionError(f"{name} must not be empty")
    result = str(value).strip()
    if not result:
        raise POSTransactionError(f"{name} must not be empty")
    return result


def _time(value: str | None = None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise POSTransactionError("timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise POSTransactionError("timestamp must be timezone-aware")
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
        raise POSTransactionError("value must be JSON-compatible") from exc


@dataclass(frozen=True)
class Evidence:
    source: str
    entity_type: str
    entity_id: str
    organization_id: str
    workspace_id: str
    project_id: str
    environment_id: str
    snapshot_ref: str
    status: str | None = None

    def validate(self) -> None:
        if str(self.source).strip() != "kernel.commerce":
            raise POSTransactionError(
                "authority evidence must come from kernel.commerce"
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
class POSCartLine:
    line_id: str
    order_item_id: str
    product_id: str
    product_variant_id: str
    inventory_item_id: str
    quantity: int
    unit_price_minor: int
    currency: str
    expected_quantity_on_hand: int
    expected_quantity_reserved: int
    product_evidence: Evidence
    variant_evidence: Evidence
    inventory_evidence: Evidence

    def validate_basic(self) -> None:
        for name, value in {
            "line_id": self.line_id,
            "order_item_id": self.order_item_id,
            "product_id": self.product_id,
            "product_variant_id": self.product_variant_id,
            "inventory_item_id": self.inventory_item_id,
            "currency": self.currency,
        }.items():
            _text(name, value)

        if (
            not isinstance(self.quantity, int)
            or isinstance(self.quantity, bool)
            or self.quantity <= 0
        ):
            raise POSTransactionError(
                "cart quantity must be an integer > 0"
            )

        if (
            not isinstance(self.unit_price_minor, int)
            or isinstance(self.unit_price_minor, bool)
            or self.unit_price_minor < 0
        ):
            raise POSTransactionError(
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
                raise POSTransactionError(
                    f"{name} must be an integer >= 0"
                )


@dataclass(frozen=True)
class POSCartSession:
    cart_id: str
    store_id: str
    branch_id: str
    currency: str
    customer_id: str | None
    lines: tuple[POSCartLine, ...]
    updated_at: str
    state: str = "TRANSIENT_POS_CART_SESSION"


@dataclass(frozen=True)
class POSCheckoutPlan:
    checkout_id: str
    transaction_id: str
    cart_id: str
    order_id: str
    store_id: str
    branch_id: str
    subtotal_minor: int
    discount_minor: int
    tax_minor: int
    total_minor: int
    currency: str
    lines: tuple[POSCartLine, ...]
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


@dataclass(frozen=True)
class ReceiptPlan:
    receipt_id: str
    order_id: str
    payment_id: str
    store_id: str
    branch_id: str
    currency: str
    subtotal_minor: int
    discount_minor: int
    tax_minor: int
    total_minor: int
    tender_type: str
    tendered_minor: int | None
    change_minor: int | None
    provider_reference: str | None
    lines: tuple[dict[str, Any], ...]
    issued_at: str
    correlation_id: str
    state: str = "READY_FOR_RECEIPT_RENDERER_AFTER_COMMIT"


@dataclass(frozen=True)
class POSSettlementPlan:
    settlement_id: str
    payment_id: str
    order_id: str
    payment_create: Any | None
    payment_transitions: tuple[Any, ...]
    inventory_deductions: tuple[Any, ...]
    order_transitions: tuple[Any, ...]
    receipt: ReceiptPlan
    transaction_requirement: str = "KERNEL_ATOMIC_TRANSACTION"
    event_publication: str = "OUTBOX_AFTER_COMMIT"
    failure_policy: str = "ROLLBACK_ALL_MUTATIONS"
    state: str = "READY_FOR_KERNEL_TRANSACTION_ADAPTER"


@dataclass(frozen=True)
class POSCardPaymentPlan:
    payment_id: str
    order_id: str
    payment_create: Any
    provider_operation_plan: Any
    state: str = "READY_FOR_PAYMENT_ABSTRACTION_ADAPTER"


class POSTransactionService:
    def __init__(
        self,
        *,
        foundation: Any,
        product_command_type: Any,
        staff_permission_checker: Any,
        kernel_tenant_scope_type: Any,
        kernel_resource_type: Any,
        kernel_inventory_type: Any,
        kernel_money_type: Any,
        kernel_order_state_type: Any,
        kernel_payment_state_type: Any,
        kernel_cart_transition: Any,
        kernel_currency_validator: Any,
        baas_payment_service: Any,
        baas_payment_request_type: Any,
        baas_request_context_type: Any,
    ) -> None:
        self._foundation = foundation
        self._product_command_type = product_command_type
        self._staff_permission_checker = staff_permission_checker
        self._kernel_tenant_scope_type = kernel_tenant_scope_type
        self._kernel_resource_type = kernel_resource_type
        self._kernel_inventory_type = kernel_inventory_type
        self._kernel_money_type = kernel_money_type
        self._kernel_order_state_type = kernel_order_state_type
        self._kernel_payment_state_type = kernel_payment_state_type
        self._kernel_cart_transition = kernel_cart_transition
        self._kernel_currency_validator = kernel_currency_validator
        self._baas_payment_service = baas_payment_service
        self._baas_payment_request_type = baas_payment_request_type
        self._baas_request_context_type = baas_request_context_type

        self._cart_sessions: dict[str, POSCartSession] = {}
        self._checkout_idempotency: dict[
            tuple[str, str, str], tuple[str, str]
        ] = {}
        self._cash_settlement_idempotency: dict[
            tuple[str, str, str], tuple[str, str]
        ] = {}

    def _validate_context(
        self,
        context: Any,
        permission: str,
    ) -> None:
        if hasattr(context, "validate"):
            context.validate()

        if str(getattr(context, "product", "")).strip().upper() != "POS":
            raise POSTransactionError("POS transaction service requires product=POS")

        if getattr(context, "store_id", None) is None:
            raise POSTransactionError("POS transaction requires store context")

        if getattr(context, "branch_id", None) is None:
            raise POSTransactionError("POS transaction requires branch context")

        try:
            allowed = self._staff_permission_checker(
                context,
                context.actor_id,
                permission,
            )
        except Exception as exc:
            raise POSTransactionError(
                f"POS staff permission check failed: {permission}"
            ) from exc

        if allowed is not True:
            raise POSTransactionError(
                f"POS staff missing permission: {permission}"
            )

    @staticmethod
    def _assert_evidence(
        *,
        context: Any,
        evidence: Evidence,
        entity_type: str,
        entity_id: str,
        require_status: str | None = None,
    ) -> None:
        evidence.validate()

        if str(evidence.entity_type).strip().upper() != entity_type:
            raise POSTransactionError("evidence entity_type mismatch")

        if evidence.entity_id != entity_id:
            raise POSTransactionError("evidence entity_id mismatch")

        for name in [
            "organization_id",
            "workspace_id",
            "project_id",
            "environment_id",
        ]:
            if getattr(evidence, name) != getattr(context, name):
                raise POSTransactionError(
                    "evidence tenant scope mismatch"
                )

        if (
            require_status is not None
            and str(evidence.status or "").strip().upper()
            != require_status
        ):
            raise POSTransactionError(
                f"{entity_type} must be {require_status}"
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

    def _validate_inventory(
        self,
        *,
        context: Any,
        line: POSCartLine,
        quantity_on_hand: int,
        quantity_reserved: int,
        timestamp: str,
    ) -> None:
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
            store_id=context.store_id,
            branch_id=context.branch_id,
            quantity_on_hand=quantity_on_hand,
            quantity_reserved=quantity_reserved,
        )

        try:
            item.validate()
        except Exception as exc:
            raise POSTransactionError(
                "Kernel InventoryItem validation failed"
            ) from exc

    def _validate_line(
        self,
        *,
        context: Any,
        line: POSCartLine,
        currency: str,
    ) -> POSCartLine:
        line.validate_basic()

        self._assert_evidence(
            context=context,
            evidence=line.product_evidence,
            entity_type="PRODUCT",
            entity_id=line.product_id,
            require_status="ACTIVE",
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

        normalized = self._kernel_currency_validator(
            line.currency
        )
        if normalized != currency:
            raise POSTransactionError(
                "all POS cart lines must use cart currency"
            )

        money = self._kernel_money_type(
            amount_minor=line.unit_price_minor,
            currency=normalized,
        )
        try:
            money.validate()
        except Exception as exc:
            raise POSTransactionError(
                "Kernel rejected POS line price"
            ) from exc

        self._validate_inventory(
            context=context,
            line=line,
            quantity_on_hand=line.expected_quantity_on_hand,
            quantity_reserved=(
                line.expected_quantity_reserved
                + line.quantity
            ),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        return line

    def open_cart(
        self,
        *,
        context: Any,
        cart_id: str,
        currency: str,
        customer_id: str | None,
        store_evidence: Evidence,
        customer_evidence: Evidence | None,
        idempotency_key: str,
        requested_at: str,
    ) -> dict[str, Any]:
        self._validate_context(
            context,
            "pos.cart.create",
        )

        self._assert_evidence(
            context=context,
            evidence=store_evidence,
            entity_type="STORE",
            entity_id=context.store_id,
            require_status="ACTIVE",
        )

        if customer_id is not None:
            if customer_evidence is None:
                raise POSTransactionError(
                    "customer evidence required for customer cart"
                )
            self._assert_evidence(
                context=context,
                evidence=customer_evidence,
                entity_type="CUSTOMER",
                entity_id=customer_id,
            )

        normalized_currency = self._kernel_currency_validator(
            currency
        )
        timestamp = _time(requested_at)

        result = self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="CART",
                entity_id=_text("cart_id", cart_id),
                context=context,
                idempotency_key=_text(
                    "idempotency_key",
                    idempotency_key,
                ),
                input_metadata={
                    "store_id": context.store_id,
                    "customer_id": customer_id,
                    "status": "OPEN",
                    "currency": normalized_currency,
                    "requested_at": timestamp,
                    "cart_line_persistence": (
                        "TRANSIENT_POS_SESSION_PENDING_SHARED_CART_ITEM"
                    ),
                },
            )
        )

        existing = self._cart_sessions.get(cart_id)
        session = POSCartSession(
            cart_id=cart_id,
            store_id=context.store_id,
            branch_id=context.branch_id,
            currency=normalized_currency,
            customer_id=customer_id,
            lines=(
                existing.lines
                if existing is not None
                else tuple()
            ),
            updated_at=timestamp,
        )
        self._cart_sessions[cart_id] = session

        return {
            **result,
            "session": session,
        }

    def upsert_cart_line(
        self,
        *,
        context: Any,
        cart_id: str,
        line: POSCartLine,
        updated_at: str | None = None,
    ) -> POSCartSession:
        self._validate_context(
            context,
            "pos.cart.update",
        )

        session = self._require_cart(
            context=context,
            cart_id=cart_id,
        )

        line = self._validate_line(
            context=context,
            line=line,
            currency=session.currency,
        )

        by_id = {
            item.line_id: item
            for item in session.lines
        }
        by_id[line.line_id] = line

        updated = replace(
            session,
            lines=tuple(
                by_id[key]
                for key in sorted(by_id)
            ),
            updated_at=_time(updated_at),
        )
        self._cart_sessions[cart_id] = updated
        return updated

    def remove_cart_line(
        self,
        *,
        context: Any,
        cart_id: str,
        line_id: str,
        updated_at: str | None = None,
    ) -> POSCartSession:
        self._validate_context(
            context,
            "pos.cart.update",
        )

        session = self._require_cart(
            context=context,
            cart_id=cart_id,
        )

        line_id = _text(
            "line_id",
            line_id,
        )

        if line_id not in {
            item.line_id
            for item in session.lines
        }:
            raise POSTransactionError(
                "POS cart line not found"
            )

        updated = replace(
            session,
            lines=tuple(
                item
                for item in session.lines
                if item.line_id != line_id
            ),
            updated_at=_time(updated_at),
        )
        self._cart_sessions[cart_id] = updated
        return updated

    def plan_checkout(
        self,
        *,
        context: Any,
        checkout_id: str,
        cart_evidence: Evidence,
        order_id: str,
        idempotency_key: str,
        requested_at: str,
    ) -> dict[str, Any]:
        self._validate_context(
            context,
            "pos.checkout.execute",
        )

        session = self._require_cart(
            context=context,
            cart_id=cart_evidence.entity_id,
        )

        if not session.lines:
            raise POSTransactionError(
                "POS checkout requires at least one cart line"
            )

        self._assert_evidence(
            context=context,
            evidence=cart_evidence,
            entity_type="CART",
            entity_id=session.cart_id,
            require_status="OPEN",
        )

        timestamp = _time(requested_at)

        line_material = []
        subtotal_minor = 0

        for line in session.lines:
            self._validate_line(
                context=context,
                line=line,
                currency=session.currency,
            )
            line_total = (
                line.quantity
                * line.unit_price_minor
            )
            subtotal_minor += line_total
            line_material.append({
                "line_id": line.line_id,
                "order_item_id": line.order_item_id,
                "product_id": line.product_id,
                "product_variant_id": line.product_variant_id,
                "inventory_item_id": line.inventory_item_id,
                "quantity": line.quantity,
                "unit_price_minor": line.unit_price_minor,
                "total_minor": line_total,
                "currency": session.currency,
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
            })

        material = {
            "checkout_id": checkout_id,
            "cart_id": session.cart_id,
            "order_id": order_id,
            "store_id": context.store_id,
            "branch_id": context.branch_id,
            "customer_id": session.customer_id,
            "currency": session.currency,
            "lines": line_material,
        }

        fingerprint = sha256(
            _canonical(material).encode("utf-8")
        ).hexdigest()

        scope = (
            context.organization_id,
            context.environment_id,
            _text(
                "idempotency_key",
                idempotency_key,
            ),
        )
        existing = self._checkout_idempotency.get(scope)

        if existing is not None:
            old_hash, transaction_id = existing
            if old_hash != fingerprint:
                raise POSTransactionError(
                    "checkout idempotency key reused with different request"
                )
            created = False
        else:
            transaction_id = (
                "pos_checkout_tx_"
                + sha256(
                    _canonical({
                        "scope": scope,
                        "fingerprint": fingerprint,
                    }).encode("utf-8")
                ).hexdigest()[:24]
            )
            self._checkout_idempotency[scope] = (
                fingerprint,
                transaction_id,
            )
            created = True

        reservations = []
        order_items = []

        for line in session.lines:
            target_reserved = (
                line.expected_quantity_reserved
                + line.quantity
            )

            self._validate_inventory(
                context=context,
                line=line,
                quantity_on_hand=(
                    line.expected_quantity_on_hand
                ),
                quantity_reserved=target_reserved,
                timestamp=timestamp,
            )

            reservations.append(
                self._foundation.plan(
                    self._product_command_type(
                        action="UPDATE",
                        entity_type="INVENTORY_ITEM",
                        entity_id=line.inventory_item_id,
                        context=context,
                        idempotency_key=(
                            f"{idempotency_key}:reserve:{line.inventory_item_id}"
                        ),
                        input_metadata={
                            "expected_quantity_on_hand": (
                                line.expected_quantity_on_hand
                            ),
                            "expected_quantity_reserved": (
                                line.expected_quantity_reserved
                            ),
                            "target_quantity_on_hand": (
                                line.expected_quantity_on_hand
                            ),
                            "target_quantity_reserved": (
                                target_reserved
                            ),
                            "quantity_reserved_delta": (
                                line.quantity
                            ),
                            "reason": "POS_CHECKOUT_RESERVATION",
                            "source_ref": (
                                f"pos-checkout://{checkout_id}"
                            ),
                            "persistence_requirement": (
                                "ATOMIC_COMPARE_EXPECTED_AND_UPDATE"
                            ),
                            "requested_at": timestamp,
                        },
                    )
                )["plan"]
            )

            order_items.append(
                self._foundation.plan(
                    self._product_command_type(
                        action="CREATE",
                        entity_type="ORDER_ITEM",
                        entity_id=line.order_item_id,
                        context=context,
                        idempotency_key=(
                            f"{idempotency_key}:order-item:{line.order_item_id}"
                        ),
                        input_metadata={
                            "order_id": order_id,
                            "product_id": line.product_id,
                            "product_variant_id": (
                                line.product_variant_id
                            ),
                            "quantity": line.quantity,
                            "unit_price_minor": (
                                line.unit_price_minor
                            ),
                            "total_minor": (
                                line.quantity
                                * line.unit_price_minor
                            ),
                            "currency": session.currency,
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
                entity_id=order_id,
                context=context,
                idempotency_key=(
                    f"{idempotency_key}:order"
                ),
                input_metadata={
                    "store_id": context.store_id,
                    "branch_id": context.branch_id,
                    "customer_id": session.customer_id,
                    "cart_id": session.cart_id,
                    "status": "DRAFT",
                    "currency": session.currency,
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
            placed = self._kernel_order_state_type(
                order_id=order_id,
                status="DRAFT",
            ).transition("PLACED")
        except Exception as exc:
            raise POSTransactionError(
                "Kernel rejected POS Cart/Order checkout transition"
            ) from exc

        cart_transition = self._foundation.plan(
            self._product_command_type(
                action="TRANSITION",
                entity_type="CART",
                entity_id=session.cart_id,
                context=context,
                idempotency_key=(
                    f"{idempotency_key}:cart-convert"
                ),
                input_metadata={
                    "from_status": "OPEN",
                    "to_status": cart_target,
                    "order_id": order_id,
                    "requested_at": timestamp,
                },
            )
        )["plan"]

        order_transition = self._foundation.plan(
            self._product_command_type(
                action="TRANSITION",
                entity_type="ORDER",
                entity_id=order_id,
                context=context,
                idempotency_key=(
                    f"{idempotency_key}:order-place"
                ),
                input_metadata={
                    "from_status": "DRAFT",
                    "to_status": placed.status,
                    "requested_at": timestamp,
                },
            )
        )["plan"]

        plan = POSCheckoutPlan(
            checkout_id=checkout_id,
            transaction_id=transaction_id,
            cart_id=session.cart_id,
            order_id=order_id,
            store_id=context.store_id,
            branch_id=context.branch_id,
            subtotal_minor=subtotal_minor,
            discount_minor=0,
            tax_minor=0,
            total_minor=subtotal_minor,
            currency=session.currency,
            lines=session.lines,
            inventory_reservations=tuple(
                reservations
            ),
            order_create=order_create,
            order_items=tuple(
                order_items
            ),
            cart_transition=cart_transition,
            order_transition=order_transition,
            correlation_id=context.correlation_id,
            kernel_authorization_ref=(
                context.kernel_authorization_ref
            ),
        )

        return {
            "created": created,
            "plan": plan,
        }

    def plan_cash_settlement(
        self,
        *,
        context: Any,
        checkout_plan: POSCheckoutPlan,
        order_evidence: Evidence,
        tendered_minor: int,
        idempotency_key: str,
        settled_at: str,
    ) -> dict[str, Any]:
        self._validate_context(
            context,
            "pos.payment.cash.record",
        )

        self._validate_checkout_for_settlement(
            context=context,
            checkout_plan=checkout_plan,
            order_evidence=order_evidence,
        )

        if (
            not isinstance(tendered_minor, int)
            or isinstance(tendered_minor, bool)
            or tendered_minor < checkout_plan.total_minor
        ):
            raise POSTransactionError(
                "cash tender must be integer minor units >= Order total"
            )

        timestamp = _time(settled_at)
        change_minor = (
            tendered_minor
            - checkout_plan.total_minor
        )

        material = {
            "order_id": checkout_plan.order_id,
            "total_minor": checkout_plan.total_minor,
            "currency": checkout_plan.currency,
            "tendered_minor": tendered_minor,
        }
        fingerprint = sha256(
            _canonical(material).encode("utf-8")
        ).hexdigest()

        scope = (
            context.organization_id,
            context.environment_id,
            _text(
                "idempotency_key",
                idempotency_key,
            ),
        )

        existing = self._cash_settlement_idempotency.get(
            scope
        )

        if existing is not None:
            old_hash, settlement_id = existing
            if old_hash != fingerprint:
                raise POSTransactionError(
                    "cash settlement idempotency conflict"
                )
            created = False
        else:
            settlement_id = (
                "pos_cash_settlement_"
                + sha256(
                    _canonical({
                        "scope": scope,
                        "fingerprint": fingerprint,
                    }).encode("utf-8")
                ).hexdigest()[:24]
            )
            self._cash_settlement_idempotency[scope] = (
                fingerprint,
                settlement_id,
            )
            created = True

        payment_id = (
            "payment_cash_"
            + sha256(
                (
                    f"{checkout_plan.order_id}"
                    f"\x1f{idempotency_key}"
                ).encode("utf-8")
            ).hexdigest()[:24]
        )

        money = self._kernel_money_type(
            amount_minor=checkout_plan.total_minor,
            currency=checkout_plan.currency,
        )
        money.validate()

        payment_create = self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="PAYMENT",
                entity_id=payment_id,
                context=context,
                idempotency_key=(
                    f"{idempotency_key}:payment"
                ),
                input_metadata={
                    "order_id": checkout_plan.order_id,
                    "status": "PENDING",
                    "amount_minor": checkout_plan.total_minor,
                    "currency": checkout_plan.currency,
                    "provider_id": "CASH",
                    "provider_reference": (
                        f"cash://{settlement_id}"
                    ),
                    "requested_at": timestamp,
                },
            )
        )["plan"]

        payment_transitions = self._explicit_cash_transitions(
            context=context,
            payment_id=payment_id,
            order_id=checkout_plan.order_id,
            money=money,
            idempotency_key=idempotency_key,
            provider_reference=(
                f"cash://{settlement_id}"
            ),
        )

        settlement = self._build_successful_settlement(
            context=context,
            checkout_plan=checkout_plan,
            payment_id=payment_id,
            payment_create=payment_create,
            payment_transitions=payment_transitions,
            tender_type="CASH",
            tendered_minor=tendered_minor,
            change_minor=change_minor,
            provider_reference=(
                f"cash://{settlement_id}"
            ),
            settlement_id=settlement_id,
            settled_at=timestamp,
            idempotency_key=idempotency_key,
        )

        return {
            "created": created,
            "plan": settlement,
        }

    def plan_card_payment(
        self,
        *,
        context: Any,
        checkout_plan: POSCheckoutPlan,
        order_evidence: Evidence,
        provider_id: str,
        payment_request_id: str,
        idempotency_key: str,
        requested_at: str,
    ) -> POSCardPaymentPlan:
        self._validate_context(
            context,
            "pos.payment.card.record",
        )

        self._validate_checkout_for_settlement(
            context=context,
            checkout_plan=checkout_plan,
            order_evidence=order_evidence,
        )

        timestamp = _time(requested_at)
        request = self._baas_payment_request_type(
            payment_request_id=_text(
                "payment_request_id",
                payment_request_id,
            ),
            source_type="ORDER",
            source_ref=checkout_plan.order_id,
            amount_minor=checkout_plan.total_minor,
            currency=checkout_plan.currency,
            capture_mode="AUTHORIZE_CAPTURE",
            idempotency_key=_text(
                "idempotency_key",
                idempotency_key,
            ),
            requested_at=timestamp,
        )

        baas_context = self._baas_context(
            context=context,
            operation="pos.card_payment.plan",
            idempotency_key=idempotency_key,
        )

        result = self._baas_payment_service.create_payment_plan(
            provider_id=_text(
                "provider_id",
                provider_id,
            ),
            request=request,
            request_context=baas_context,
        )
        provider_plan = result["plan"]

        payment_create = self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="PAYMENT",
                entity_id=provider_plan.payment_id,
                context=context,
                idempotency_key=(
                    f"{idempotency_key}:payment"
                ),
                input_metadata={
                    "order_id": checkout_plan.order_id,
                    "status": "PENDING",
                    "amount_minor": checkout_plan.total_minor,
                    "currency": checkout_plan.currency,
                    "provider_id": provider_plan.provider_id,
                    "provider_reference": None,
                    "requested_at": timestamp,
                },
            )
        )["plan"]

        return POSCardPaymentPlan(
            payment_id=provider_plan.payment_id,
            order_id=checkout_plan.order_id,
            payment_create=payment_create,
            provider_operation_plan=provider_plan,
        )

    def plan_card_result(
        self,
        *,
        context: Any,
        checkout_plan: POSCheckoutPlan,
        order_evidence: Evidence,
        payment_evidence: Evidence,
        provider_result: Any,
        kernel_payment_status: str,
        settled_at: str,
    ) -> POSSettlementPlan | tuple[Any, ...]:
        self._validate_context(
            context,
            "pos.payment.card.record",
        )

        self._validate_checkout_for_settlement(
            context=context,
            checkout_plan=checkout_plan,
            order_evidence=order_evidence,
        )

        self._assert_evidence(
            context=context,
            evidence=payment_evidence,
            entity_type="PAYMENT",
            entity_id=provider_result.payment_id,
        )

        baas_context = self._baas_context(
            context=context,
            operation="pos.card_payment.provider_result",
            idempotency_key=(
                f"{provider_result.payment_id}:"
                f"{provider_result.provider_reference}:"
                f"{provider_result.outcome}"
            ),
        )

        transition = self._baas_payment_service.plan_provider_result(
            result=provider_result,
            kernel_current_status=str(
                kernel_payment_status
            ).strip().upper(),
            request_context=baas_context,
        )

        commands = []
        prior = transition.from_status

        for target in transition.transition_sequence:
            commands.append(
                self._foundation.plan(
                    self._product_command_type(
                        action="TRANSITION",
                        entity_type="PAYMENT",
                        entity_id=transition.payment_id,
                        context=context,
                        idempotency_key=(
                            f"card-payment:{transition.payment_id}:"
                            f"{transition.provider_reference}:{prior}:{target}"
                        ),
                        input_metadata={
                            "from_status": prior,
                            "to_status": target,
                            "provider_id": transition.provider_id,
                            "provider_reference": (
                                transition.provider_reference
                            ),
                            "amount_minor": transition.amount_minor,
                            "currency": transition.currency,
                            "reconciliation_state": (
                                transition.reconciliation_state
                            ),
                        },
                    )
                )["plan"]
            )
            prior = target

        if transition.transition_sequence[-1] != "CAPTURED":
            return tuple(commands)

        settlement_id = (
            "pos_card_settlement_"
            + sha256(
                (
                    f"{transition.payment_id}"
                    f"\x1f{transition.provider_reference}"
                ).encode("utf-8")
            ).hexdigest()[:24]
        )

        return self._build_successful_settlement(
            context=context,
            checkout_plan=checkout_plan,
            payment_id=transition.payment_id,
            payment_create=None,
            payment_transitions=tuple(commands),
            tender_type="CARD",
            tendered_minor=None,
            change_minor=None,
            provider_reference=(
                transition.provider_reference
            ),
            settlement_id=settlement_id,
            settled_at=_time(settled_at),
            idempotency_key=(
                f"card-settlement:{transition.payment_id}"
            ),
        )

    def _explicit_cash_transitions(
        self,
        *,
        context: Any,
        payment_id: str,
        order_id: str,
        money: Any,
        idempotency_key: str,
        provider_reference: str,
    ) -> tuple[Any, ...]:
        commands = []
        state = self._kernel_payment_state_type(
            payment_id=payment_id,
            order_id=order_id,
            status="PENDING",
            amount=money,
        )

        for target in [
            "AUTHORIZED",
            "CAPTURED",
        ]:
            try:
                next_state = state.transition(
                    target
                )
            except Exception as exc:
                raise POSTransactionError(
                    "Kernel rejected explicit cash Payment transition"
                ) from exc

            commands.append(
                self._foundation.plan(
                    self._product_command_type(
                        action="TRANSITION",
                        entity_type="PAYMENT",
                        entity_id=payment_id,
                        context=context,
                        idempotency_key=(
                            f"{idempotency_key}:payment:{state.status}:{target}"
                        ),
                        input_metadata={
                            "from_status": state.status,
                            "to_status": next_state.status,
                            "provider_id": "CASH",
                            "provider_reference": (
                                provider_reference
                            ),
                        },
                    )
                )["plan"]
            )
            state = next_state

        return tuple(commands)

    def _build_successful_settlement(
        self,
        *,
        context: Any,
        checkout_plan: POSCheckoutPlan,
        payment_id: str,
        payment_create: Any | None,
        payment_transitions: tuple[Any, ...],
        tender_type: str,
        tendered_minor: int | None,
        change_minor: int | None,
        provider_reference: str | None,
        settlement_id: str,
        settled_at: str,
        idempotency_key: str,
    ) -> POSSettlementPlan:
        inventory_commands = []

        for line in checkout_plan.lines:
            expected_reserved = (
                line.expected_quantity_reserved
                + line.quantity
            )
            target_on_hand = (
                line.expected_quantity_on_hand
                - line.quantity
            )
            target_reserved = (
                expected_reserved
                - line.quantity
            )

            self._validate_inventory(
                context=context,
                line=line,
                quantity_on_hand=target_on_hand,
                quantity_reserved=target_reserved,
                timestamp=settled_at,
            )

            inventory_commands.append(
                self._foundation.plan(
                    self._product_command_type(
                        action="UPDATE",
                        entity_type="INVENTORY_ITEM",
                        entity_id=line.inventory_item_id,
                        context=context,
                        idempotency_key=(
                            f"{idempotency_key}:deduct:{line.inventory_item_id}"
                        ),
                        input_metadata={
                            "expected_quantity_on_hand": (
                                line.expected_quantity_on_hand
                            ),
                            "expected_quantity_reserved": (
                                expected_reserved
                            ),
                            "target_quantity_on_hand": (
                                target_on_hand
                            ),
                            "target_quantity_reserved": (
                                target_reserved
                            ),
                            "quantity_on_hand_delta": (
                                -line.quantity
                            ),
                            "quantity_reserved_delta": (
                                -line.quantity
                            ),
                            "reason": "POS_SALE_SETTLEMENT",
                            "source_ref": (
                                f"pos-settlement://{settlement_id}"
                            ),
                            "persistence_requirement": (
                                "ATOMIC_COMPARE_EXPECTED_AND_UPDATE"
                            ),
                            "requested_at": settled_at,
                        },
                    )
                )["plan"]
            )

        try:
            confirmed = self._kernel_order_state_type(
                order_id=checkout_plan.order_id,
                status="PLACED",
            ).transition("CONFIRMED")

            completed = confirmed.transition(
                "COMPLETED"
            )
        except Exception as exc:
            raise POSTransactionError(
                "Kernel rejected POS Order settlement lifecycle"
            ) from exc

        order_transitions = (
            self._foundation.plan(
                self._product_command_type(
                    action="TRANSITION",
                    entity_type="ORDER",
                    entity_id=checkout_plan.order_id,
                    context=context,
                    idempotency_key=(
                        f"{idempotency_key}:order-confirm"
                    ),
                    input_metadata={
                        "from_status": "PLACED",
                        "to_status": confirmed.status,
                        "payment_id": payment_id,
                        "requested_at": settled_at,
                    },
                )
            )["plan"],
            self._foundation.plan(
                self._product_command_type(
                    action="TRANSITION",
                    entity_type="ORDER",
                    entity_id=checkout_plan.order_id,
                    context=context,
                    idempotency_key=(
                        f"{idempotency_key}:order-complete"
                    ),
                    input_metadata={
                        "from_status": confirmed.status,
                        "to_status": completed.status,
                        "payment_id": payment_id,
                        "requested_at": settled_at,
                    },
                )
            )["plan"],
        )

        receipt = self._receipt(
            context=context,
            checkout_plan=checkout_plan,
            payment_id=payment_id,
            tender_type=tender_type,
            tendered_minor=tendered_minor,
            change_minor=change_minor,
            provider_reference=provider_reference,
            settled_at=settled_at,
        )

        return POSSettlementPlan(
            settlement_id=settlement_id,
            payment_id=payment_id,
            order_id=checkout_plan.order_id,
            payment_create=payment_create,
            payment_transitions=payment_transitions,
            inventory_deductions=tuple(
                inventory_commands
            ),
            order_transitions=order_transitions,
            receipt=receipt,
        )

    def _receipt(
        self,
        *,
        context: Any,
        checkout_plan: POSCheckoutPlan,
        payment_id: str,
        tender_type: str,
        tendered_minor: int | None,
        change_minor: int | None,
        provider_reference: str | None,
        settled_at: str,
    ) -> ReceiptPlan:
        lines = tuple(
            {
                "product_id": line.product_id,
                "product_variant_id": line.product_variant_id,
                "quantity": line.quantity,
                "unit_price_minor": line.unit_price_minor,
                "total_minor": (
                    line.quantity
                    * line.unit_price_minor
                ),
                "currency": checkout_plan.currency,
            }
            for line in checkout_plan.lines
        )

        receipt_material = {
            "order_id": checkout_plan.order_id,
            "payment_id": payment_id,
            "store_id": context.store_id,
            "branch_id": context.branch_id,
            "total_minor": checkout_plan.total_minor,
            "currency": checkout_plan.currency,
            "tender_type": tender_type,
            "provider_reference": provider_reference,
        }

        return ReceiptPlan(
            receipt_id=(
                "receipt_"
                + sha256(
                    _canonical(
                        receipt_material
                    ).encode("utf-8")
                ).hexdigest()[:24]
            ),
            order_id=checkout_plan.order_id,
            payment_id=payment_id,
            store_id=context.store_id,
            branch_id=context.branch_id,
            currency=checkout_plan.currency,
            subtotal_minor=checkout_plan.subtotal_minor,
            discount_minor=checkout_plan.discount_minor,
            tax_minor=checkout_plan.tax_minor,
            total_minor=checkout_plan.total_minor,
            tender_type=tender_type,
            tendered_minor=tendered_minor,
            change_minor=change_minor,
            provider_reference=provider_reference,
            lines=lines,
            issued_at=settled_at,
            correlation_id=context.correlation_id,
        )

    def _validate_checkout_for_settlement(
        self,
        *,
        context: Any,
        checkout_plan: POSCheckoutPlan,
        order_evidence: Evidence,
    ) -> None:
        if checkout_plan.state != (
            "READY_FOR_KERNEL_TRANSACTION_ADAPTER"
        ):
            raise POSTransactionError(
                "settlement requires valid POS checkout plan"
            )

        if (
            checkout_plan.store_id
            != context.store_id
            or checkout_plan.branch_id
            != context.branch_id
        ):
            raise POSTransactionError(
                "checkout plan POS scope mismatch"
            )

        self._assert_evidence(
            context=context,
            evidence=order_evidence,
            entity_type="ORDER",
            entity_id=checkout_plan.order_id,
            require_status="PLACED",
        )

    def _baas_context(
        self,
        *,
        context: Any,
        operation: str,
        idempotency_key: str,
    ) -> Any:
        return self._baas_request_context_type(
            request_id=(
                "req_pos_payment_"
                + sha256(
                    (
                        f"{context.correlation_id}"
                        f"\x1f{operation}"
                        f"\x1f{idempotency_key}"
                    ).encode("utf-8")
                ).hexdigest()[:20]
            ),
            correlation_id=context.correlation_id,
            service="payments",
            operation=operation,
            organization_id=context.organization_id,
            workspace_id=context.workspace_id,
            project_id=context.project_id,
            environment_id=context.environment_id,
            actor_id=context.actor_id,
            actor_type=context.actor_type,
            kernel_authorization_ref=(
                context.kernel_authorization_ref
            ),
            idempotency_key=idempotency_key,
        )

    def _require_cart(
        self,
        *,
        context: Any,
        cart_id: str,
    ) -> POSCartSession:
        session = self._cart_sessions.get(
            _text(
                "cart_id",
                cart_id,
            )
        )

        if session is None:
            raise POSTransactionError(
                "POS transient cart session not found"
            )

        if (
            session.store_id
            != context.store_id
            or session.branch_id
            != context.branch_id
        ):
            raise POSTransactionError(
                "POS cart session branch scope mismatch"
            )

        return session
