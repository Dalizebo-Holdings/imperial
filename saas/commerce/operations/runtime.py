from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any


class CommerceOperationsError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise CommerceOperationsError(f"{name} must not be empty")
    result = str(value).strip()
    if not result:
        raise CommerceOperationsError(f"{name} must not be empty")
    return result


def _time(value: str | None = None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CommerceOperationsError("timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise CommerceOperationsError("timestamp must be timezone-aware")
    return parsed


def _canonical(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except (TypeError, ValueError) as exc:
        raise CommerceOperationsError("value must be JSON-compatible") from exc


def _validate_context(context: Any) -> None:
    if hasattr(context, "validate"):
        context.validate()

    if str(getattr(context, "product", "")).strip().upper() != "COMMERCE":
        raise CommerceOperationsError(
            "Commerce operations require product=COMMERCE"
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

    def validate(self) -> None:
        if str(self.source).strip() != "kernel.commerce":
            raise CommerceOperationsError(
                "authority evidence must come from kernel.commerce"
            )
        for name, value in self.__dict__.items():
            _text(name, value)


def _assert_evidence(
    *,
    context: Any,
    evidence: CommerceEvidence,
    entity_type: str,
    entity_id: str,
) -> None:
    evidence.validate()

    if str(evidence.entity_type).strip().upper() != entity_type:
        raise CommerceOperationsError("authority evidence entity_type mismatch")

    if evidence.entity_id != entity_id:
        raise CommerceOperationsError("authority evidence entity_id mismatch")

    for name in [
        "organization_id",
        "workspace_id",
        "project_id",
        "environment_id",
    ]:
        if getattr(evidence, name) != getattr(context, name):
            raise CommerceOperationsError(
                "authority evidence tenant scope mismatch"
            )


@dataclass(frozen=True)
class CommercePaymentPlan:
    payment_id: str
    order_id: str
    payment_record_command: Any
    provider_operation_plan: Any
    state: str = "READY_FOR_PAYMENT_ABSTRACTION_ADAPTER"


@dataclass(frozen=True)
class CommercePaymentResultPlan:
    payment_id: str
    payment_transition_commands: tuple[Any, ...]
    order_confirmation_command: Any | None
    provider_transition_plan: Any
    state: str = "READY_FOR_KERNEL_TRANSACTION_ADAPTER"


class CommercePaymentsService:
    def __init__(
        self,
        *,
        foundation: Any,
        product_command_type: Any,
        baas_payment_service: Any,
        baas_payment_request_type: Any,
        baas_request_context_type: Any,
        kernel_order_state_type: Any,
    ) -> None:
        self._foundation = foundation
        self._product_command_type = product_command_type
        self._payment_service = baas_payment_service
        self._payment_request_type = baas_payment_request_type
        self._request_context_type = baas_request_context_type
        self._kernel_order_state_type = kernel_order_state_type

    def _baas_context(
        self,
        *,
        context: Any,
        operation: str,
        idempotency_key: str,
    ) -> Any:
        return self._request_context_type(
            request_id=(
                "req_commerce_payment_"
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
            kernel_authorization_ref=context.kernel_authorization_ref,
            idempotency_key=idempotency_key,
        )

    def plan_payment(
        self,
        *,
        context: Any,
        order_evidence: CommerceEvidence,
        order_status: str,
        provider_id: str,
        payment_request_id: str,
        amount_minor: int,
        currency: str,
        capture_mode: str,
        idempotency_key: str,
        requested_at: str,
    ) -> CommercePaymentPlan:
        _validate_context(context)

        _assert_evidence(
            context=context,
            evidence=order_evidence,
            entity_type="ORDER",
            entity_id=order_evidence.entity_id,
        )

        if str(order_status).strip().upper() != "PLACED":
            raise CommerceOperationsError(
                "Commerce payment start requires PLACED Order"
            )

        if (
            not isinstance(amount_minor, int)
            or isinstance(amount_minor, bool)
            or amount_minor <= 0
        ):
            raise CommerceOperationsError(
                "payment amount_minor must be an integer > 0"
            )

        timestamp = _time(requested_at).isoformat()

        request = self._payment_request_type(
            payment_request_id=_text(
                "payment_request_id",
                payment_request_id,
            ),
            source_type="ORDER",
            source_ref=order_evidence.entity_id,
            amount_minor=amount_minor,
            currency=str(currency).strip().upper(),
            capture_mode=str(capture_mode).strip().upper(),
            idempotency_key=_text(
                "idempotency_key",
                idempotency_key,
            ),
            requested_at=timestamp,
        )

        baas_context = self._baas_context(
            context=context,
            operation="payment.plan",
            idempotency_key=idempotency_key,
        )

        result = self._payment_service.create_payment_plan(
            provider_id=_text("provider_id", provider_id),
            request=request,
            request_context=baas_context,
        )

        provider_plan = result["plan"]

        payment_record = self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="PAYMENT",
                entity_id=provider_plan.payment_id,
                context=context,
                idempotency_key=(
                    f"{idempotency_key}:payment-record"
                ),
                input_metadata={
                    "order_id": order_evidence.entity_id,
                    "status": "PENDING",
                    "amount_minor": amount_minor,
                    "currency": provider_plan.currency,
                    "provider_id": provider_plan.provider_id,
                    "provider_reference": None,
                    "reconciliation_state": "PENDING_PROVIDER_RESULT",
                    "requested_at": timestamp,
                },
            )
        )["plan"]

        return CommercePaymentPlan(
            payment_id=provider_plan.payment_id,
            order_id=order_evidence.entity_id,
            payment_record_command=payment_record,
            provider_operation_plan=provider_plan,
        )

    def plan_provider_result(
        self,
        *,
        context: Any,
        order_evidence: CommerceEvidence,
        payment_evidence: CommerceEvidence,
        provider_result: Any,
        kernel_payment_status: str,
    ) -> CommercePaymentResultPlan:
        _validate_context(context)

        _assert_evidence(
            context=context,
            evidence=order_evidence,
            entity_type="ORDER",
            entity_id=order_evidence.entity_id,
        )
        _assert_evidence(
            context=context,
            evidence=payment_evidence,
            entity_type="PAYMENT",
            entity_id=provider_result.payment_id,
        )

        baas_context = self._baas_context(
            context=context,
            operation="payment.provider_result",
            idempotency_key=(
                f"provider-result:{provider_result.payment_id}:"
                f"{provider_result.provider_reference}:"
                f"{provider_result.outcome}"
            ),
        )

        transition = self._payment_service.plan_provider_result(
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
                            f"payment-transition:{transition.payment_id}:"
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

        order_confirmation = None

        if transition.transition_sequence[-1] == "CAPTURED":
            try:
                confirmed = self._kernel_order_state_type(
                    order_id=order_evidence.entity_id,
                    status="PLACED",
                ).transition("CONFIRMED")
            except Exception as exc:
                raise CommerceOperationsError(
                    "Kernel rejected Order confirmation after capture"
                ) from exc

            order_confirmation = self._foundation.plan(
                self._product_command_type(
                    action="TRANSITION",
                    entity_type="ORDER",
                    entity_id=order_evidence.entity_id,
                    context=context,
                    idempotency_key=(
                        f"order-confirm-after-payment:"
                        f"{transition.payment_id}"
                    ),
                    input_metadata={
                        "from_status": "PLACED",
                        "to_status": confirmed.status,
                        "payment_id": transition.payment_id,
                        "provider_reference": (
                            transition.provider_reference
                        ),
                    },
                )
            )["plan"]

        return CommercePaymentResultPlan(
            payment_id=transition.payment_id,
            payment_transition_commands=tuple(commands),
            order_confirmation_command=order_confirmation,
            provider_transition_plan=transition,
        )


@dataclass(frozen=True)
class DiscountDefinition:
    discount_id: str
    discount_type: str
    value_minor: int | None
    basis_points: int | None
    currency: str | None
    idempotency_key: str

    def validate_basic(self) -> None:
        _text("discount_id", self.discount_id)
        _text("idempotency_key", self.idempotency_key)


@dataclass(frozen=True)
class DiscountQuote:
    discount_id: str
    discount_type: str
    subtotal_minor: int
    discount_minor: int
    total_minor: int
    currency: str
    quote_hash: str


@dataclass(frozen=True)
class CheckoutDiscountOverlay:
    transaction_id: str
    discount_quote: DiscountQuote
    order_create_override: Any
    subtotal_minor: int
    discount_minor: int
    tax_minor: int
    total_minor: int
    state: str = "READY_FOR_CHECKOUT_TRANSACTION_ADAPTER"


class CommerceDiscountsService:
    def __init__(
        self,
        *,
        foundation: Any,
        product_command_type: Any,
        kernel_discount_type: Any,
        kernel_currency_validator: Any,
    ) -> None:
        self._foundation = foundation
        self._product_command_type = product_command_type
        self._kernel_discount_type = kernel_discount_type
        self._kernel_currency_validator = kernel_currency_validator

    def _kernel_discount(
        self,
        definition: DiscountDefinition,
    ) -> Any:
        definition.validate_basic()

        discount = self._kernel_discount_type(
            discount_id=definition.discount_id,
            discount_type=str(
                definition.discount_type
            ).strip().upper(),
            value_minor=definition.value_minor,
            basis_points=definition.basis_points,
            currency=(
                None
                if definition.currency is None
                else str(definition.currency).strip().upper()
            ),
        )

        try:
            discount.validate()
        except Exception as exc:
            raise CommerceOperationsError(
                "Kernel Discount validation failed"
            ) from exc

        return discount

    def plan_create(
        self,
        *,
        context: Any,
        definition: DiscountDefinition,
        requested_at: str,
    ) -> dict[str, Any]:
        _validate_context(context)
        discount = self._kernel_discount(definition)

        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="DISCOUNT",
                entity_id=definition.discount_id,
                context=context,
                idempotency_key=definition.idempotency_key,
                input_metadata={
                    "discount_type": discount.discount_type,
                    "value_minor": discount.value_minor,
                    "basis_points": discount.basis_points,
                    "currency": discount.currency,
                    "requested_at": _time(requested_at).isoformat(),
                },
            )
        )

    def quote(
        self,
        *,
        definition: DiscountDefinition,
        subtotal_minor: int,
        currency: str,
    ) -> DiscountQuote:
        discount = self._kernel_discount(definition)

        if (
            not isinstance(subtotal_minor, int)
            or isinstance(subtotal_minor, bool)
            or subtotal_minor < 0
        ):
            raise CommerceOperationsError(
                "subtotal_minor must be an integer >= 0"
            )

        normalized_currency = self._kernel_currency_validator(currency)

        if discount.discount_type == "FIXED":
            if discount.currency != normalized_currency:
                raise CommerceOperationsError(
                    "fixed discount currency mismatch"
                )
            discount_minor = min(
                discount.value_minor,
                subtotal_minor,
            )
        else:
            discount_minor = (
                subtotal_minor
                * discount.basis_points
            ) // 10000

        total_minor = subtotal_minor - discount_minor

        material = {
            "discount_id": discount.discount_id,
            "discount_type": discount.discount_type,
            "subtotal_minor": subtotal_minor,
            "discount_minor": discount_minor,
            "total_minor": total_minor,
            "currency": normalized_currency,
        }

        return DiscountQuote(
            discount_id=discount.discount_id,
            discount_type=discount.discount_type,
            subtotal_minor=subtotal_minor,
            discount_minor=discount_minor,
            total_minor=total_minor,
            currency=normalized_currency,
            quote_hash=sha256(
                _canonical(material).encode("utf-8")
            ).hexdigest(),
        )

    def overlay_checkout(
        self,
        *,
        checkout_plan: Any,
        quote: DiscountQuote,
    ) -> CheckoutDiscountOverlay:
        if getattr(checkout_plan, "state", None) != (
            "READY_FOR_KERNEL_TRANSACTION_ADAPTER"
        ):
            raise CommerceOperationsError(
                "discount overlay requires unexecuted checkout plan"
            )

        if checkout_plan.subtotal_minor != quote.subtotal_minor:
            raise CommerceOperationsError(
                "discount quote subtotal does not match checkout"
            )

        if checkout_plan.currency != quote.currency:
            raise CommerceOperationsError(
                "discount quote currency does not match checkout"
            )

        order_create = checkout_plan.order_create
        metadata = dict(order_create.input_metadata)

        if metadata.get("status") != "DRAFT":
            raise CommerceOperationsError(
                "discount overlay requires DRAFT Order creation"
            )

        metadata["discount_minor"] = quote.discount_minor
        metadata["total_minor"] = quote.total_minor
        metadata["discount_quote_hash"] = quote.quote_hash
        metadata["discount_id"] = quote.discount_id

        order_override = replace(
            order_create,
            input_metadata=metadata,
        )

        return CheckoutDiscountOverlay(
            transaction_id=checkout_plan.transaction_id,
            discount_quote=quote,
            order_create_override=order_override,
            subtotal_minor=quote.subtotal_minor,
            discount_minor=quote.discount_minor,
            tax_minor=checkout_plan.tax_minor,
            total_minor=quote.total_minor + checkout_plan.tax_minor,
        )


NOTIFICATION_CHANNELS = {
    "WEBHOOK",
    "INTERNAL",
}


@dataclass(frozen=True)
class NotificationRequest:
    event_type: str
    resource_type: str
    resource_id: str
    template_ref: str
    recipient_ref: str
    channel: str
    target_ref: str
    idempotency_key: str
    occurred_at: str

    def validate(self) -> None:
        for name, value in {
            "event_type": self.event_type,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "template_ref": self.template_ref,
            "recipient_ref": self.recipient_ref,
            "target_ref": self.target_ref,
            "idempotency_key": self.idempotency_key,
        }.items():
            _text(name, value)

        if str(self.channel).strip().upper() not in NOTIFICATION_CHANNELS:
            raise CommerceOperationsError(
                "P0 notification channel must be WEBHOOK or INTERNAL"
            )

        if not str(self.template_ref).startswith("template://"):
            raise CommerceOperationsError(
                "template_ref must use template://"
            )

        if not (
            str(self.recipient_ref).startswith("customer://")
            or str(self.recipient_ref).startswith("organization://")
            or str(self.recipient_ref).startswith("user://")
        ):
            raise CommerceOperationsError(
                "recipient_ref must be an opaque identity reference"
            )

        _time(self.occurred_at)


@dataclass(frozen=True)
class NotificationPlan:
    notification_id: str
    event_type: str
    resource_type: str
    resource_id: str
    channel: str
    target_ref: str
    template_ref: str
    recipient_ref: str
    tenant_context: dict[str, str]
    correlation_id: str
    idempotency_key: str
    publication: str = "OUTBOX_AFTER_COMMIT"
    state: str = "READY_FOR_POST_COMMIT_EVENTS_ADAPTER"


class CommerceNotificationsService:
    def __init__(self) -> None:
        self._idempotency: dict[
            tuple[str, str, str],
            tuple[str, str],
        ] = {}

    def plan(
        self,
        *,
        context: Any,
        request: NotificationRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        request.validate()

        material = {
            "event_type": request.event_type,
            "resource_type": request.resource_type,
            "resource_id": request.resource_id,
            "template_ref": request.template_ref,
            "recipient_ref": request.recipient_ref,
            "channel": str(request.channel).strip().upper(),
            "target_ref": request.target_ref,
        }

        fingerprint = sha256(
            _canonical(material).encode("utf-8")
        ).hexdigest()

        scope = (
            context.organization_id,
            context.environment_id,
            request.idempotency_key,
        )

        existing = self._idempotency.get(scope)
        created = True

        if existing is not None:
            existing_hash, notification_id = existing
            if existing_hash != fingerprint:
                raise CommerceOperationsError(
                    "notification idempotency key reused with different intent"
                )
            created = False
        else:
            notification_id = (
                "notification_"
                + sha256(
                    _canonical(
                        {
                            "scope": scope,
                            "fingerprint": fingerprint,
                        }
                    ).encode("utf-8")
                ).hexdigest()[:24]
            )
            self._idempotency[scope] = (
                fingerprint,
                notification_id,
            )

        plan = NotificationPlan(
            notification_id=notification_id,
            event_type=request.event_type,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            channel=str(request.channel).strip().upper(),
            target_ref=request.target_ref,
            template_ref=request.template_ref,
            recipient_ref=request.recipient_ref,
            tenant_context={
                "organization_id": context.organization_id,
                "workspace_id": context.workspace_id,
                "project_id": context.project_id,
                "environment_id": context.environment_id,
            },
            correlation_id=context.correlation_id,
            idempotency_key=request.idempotency_key,
        )

        return {
            "created": created,
            "plan": plan,
        }


DASHBOARD_METRICS = (
    "order_count",
    "gross_sales_minor",
    "captured_payment_count",
    "customer_count",
    "low_stock_item_count",
)


@dataclass(frozen=True)
class DashboardQuery:
    period_start: str
    period_end: str
    currency: str
    low_stock_threshold: int = 5

    def validate(self) -> None:
        start = _time(self.period_start)
        end = _time(self.period_end)

        if start >= end:
            raise CommerceOperationsError(
                "dashboard period_start must be before period_end"
            )

        if (end - start).days > 366:
            raise CommerceOperationsError(
                "dashboard query window may not exceed 366 days"
            )

        if (
            not isinstance(self.low_stock_threshold, int)
            or isinstance(self.low_stock_threshold, bool)
            or self.low_stock_threshold < 0
        ):
            raise CommerceOperationsError(
                "low_stock_threshold must be an integer >= 0"
            )

        _text("currency", self.currency)


@dataclass(frozen=True)
class DashboardReadPlan:
    query_id: str
    tenant_context: dict[str, str]
    store_id: str
    period_start: str
    period_end: str
    currency: str
    metrics: tuple[str, ...]
    sources: tuple[str, ...]
    filters: dict[str, Any]
    correlation_id: str
    state: str = "READY_FOR_DASHBOARD_READ_ADAPTER"


class CommerceDashboardService:
    def __init__(
        self,
        *,
        kernel_currency_validator: Any,
    ) -> None:
        self._kernel_currency_validator = kernel_currency_validator

    def plan(
        self,
        *,
        context: Any,
        query: DashboardQuery,
    ) -> DashboardReadPlan:
        _validate_context(context)
        query.validate()

        if context.store_id is None:
            raise CommerceOperationsError(
                "Commerce Dashboard requires store context"
            )

        start = _time(query.period_start)
        end = _time(query.period_end)
        currency = self._kernel_currency_validator(
            query.currency
        )

        material = {
            "organization_id": context.organization_id,
            "workspace_id": context.workspace_id,
            "project_id": context.project_id,
            "environment_id": context.environment_id,
            "store_id": context.store_id,
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "currency": currency,
            "low_stock_threshold": query.low_stock_threshold,
            "metrics": DASHBOARD_METRICS,
        }

        return DashboardReadPlan(
            query_id=(
                "commerce_dashboard_"
                + sha256(
                    _canonical(material).encode("utf-8")
                ).hexdigest()[:24]
            ),
            tenant_context={
                "organization_id": context.organization_id,
                "workspace_id": context.workspace_id,
                "project_id": context.project_id,
                "environment_id": context.environment_id,
            },
            store_id=context.store_id,
            period_start=start.isoformat(),
            period_end=end.isoformat(),
            currency=currency,
            metrics=DASHBOARD_METRICS,
            sources=(
                "kernel.commerce.orders",
                "kernel.commerce.order_items",
                "kernel.commerce.payments",
                "kernel.commerce.customers",
                "kernel.commerce.inventory_items",
                "kernel.audit",
            ),
            filters={
                "store_id": context.store_id,
                "currency": currency,
                "low_stock_threshold": query.low_stock_threshold,
            },
            correlation_id=context.correlation_id,
        )
