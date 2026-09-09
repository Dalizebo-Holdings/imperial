from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
import json
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


TENDERS = {
    "CASH",
    "CARD",
}

SUMMARY_METRICS = (
    "completed_order_count",
    "gross_sales_minor",
    "cash_sales_minor",
    "card_sales_minor",
    "refund_count",
    "refund_minor",
    "net_sales_minor",
    "items_sold",
    "items_returned",
)


class POSReturnsError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise POSReturnsError(
            f"{name} must not be empty"
        )
    result = str(value).strip()
    if not result:
        raise POSReturnsError(
            f"{name} must not be empty"
        )
    return result


def _iso(value: str | None = None) -> str:
    if value is None:
        return datetime.now(
            timezone.utc
        ).isoformat()

    try:
        parsed = datetime.fromisoformat(
            value
        )
    except ValueError as exc:
        raise POSReturnsError(
            "timestamp must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise POSReturnsError(
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
        raise POSReturnsError(
            "return material must be JSON-compatible"
        ) from exc


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
        if (
            str(
                self.source
            ).strip()
            != "kernel.commerce"
        ):
            raise POSReturnsError(
                "authority evidence must come from kernel.commerce"
            )

        for name, value in {
            "entity_type": (
                self.entity_type
            ),
            "entity_id": (
                self.entity_id
            ),
            "organization_id": (
                self.organization_id
            ),
            "workspace_id": (
                self.workspace_id
            ),
            "project_id": (
                self.project_id
            ),
            "environment_id": (
                self.environment_id
            ),
            "snapshot_ref": (
                self.snapshot_ref
            ),
        }.items():
            _text(
                name,
                value,
            )


@dataclass(frozen=True)
class ReturnLine:
    return_line_id: str
    order_item_id: str
    product_id: str
    product_variant_id: str
    inventory_item_id: str
    sold_quantity: int
    previously_returned_quantity: int
    return_quantity: int
    unit_price_minor: int
    currency: str
    current_quantity_on_hand: int
    current_quantity_reserved: int
    product_evidence: Evidence
    variant_evidence: Evidence
    inventory_evidence: Evidence

    def validate_basic(self) -> None:
        for name, value in {
            "return_line_id": (
                self.return_line_id
            ),
            "order_item_id": (
                self.order_item_id
            ),
            "product_id": (
                self.product_id
            ),
            "product_variant_id": (
                self.product_variant_id
            ),
            "inventory_item_id": (
                self.inventory_item_id
            ),
            "currency": (
                self.currency
            ),
        }.items():
            _text(
                name,
                value,
            )

        for name, value in {
            "sold_quantity": (
                self.sold_quantity
            ),
            "previously_returned_quantity": (
                self.previously_returned_quantity
            ),
            "return_quantity": (
                self.return_quantity
            ),
            "unit_price_minor": (
                self.unit_price_minor
            ),
            "current_quantity_on_hand": (
                self.current_quantity_on_hand
            ),
            "current_quantity_reserved": (
                self.current_quantity_reserved
            ),
        }.items():
            if (
                not isinstance(
                    value,
                    int,
                )
                or isinstance(
                    value,
                    bool,
                )
            ):
                raise POSReturnsError(
                    f"{name} must be an integer"
                )

        if self.sold_quantity <= 0:
            raise POSReturnsError(
                "sold_quantity must be > 0"
            )

        if (
            self.previously_returned_quantity
            < 0
        ):
            raise POSReturnsError(
                "previously_returned_quantity must be >= 0"
            )

        if self.return_quantity <= 0:
            raise POSReturnsError(
                "return_quantity must be > 0"
            )

        if (
            self.previously_returned_quantity
            + self.return_quantity
            > self.sold_quantity
        ):
            raise POSReturnsError(
                "returned quantity may not exceed sold quantity"
            )

        if self.unit_price_minor < 0:
            raise POSReturnsError(
                "unit_price_minor must be >= 0"
            )

        if (
            self.current_quantity_on_hand < 0
            or self.current_quantity_reserved < 0
        ):
            raise POSReturnsError(
                "current inventory quantities must be >= 0"
            )


@dataclass(frozen=True)
class ReturnRequest:
    return_id: str
    refund_id: str
    order_id: str
    payment_id: str
    tender_type: str
    captured_amount_minor: int
    previously_refunded_minor: int
    currency: str
    reason: str
    lines: tuple[
        ReturnLine,
        ...
    ]
    idempotency_key: str
    requested_at: str

    def validate_basic(self) -> None:
        for name, value in {
            "return_id": (
                self.return_id
            ),
            "refund_id": (
                self.refund_id
            ),
            "order_id": (
                self.order_id
            ),
            "payment_id": (
                self.payment_id
            ),
            "currency": (
                self.currency
            ),
            "reason": (
                self.reason
            ),
            "idempotency_key": (
                self.idempotency_key
            ),
        }.items():
            _text(
                name,
                value,
            )

        if (
            str(
                self.tender_type
            ).strip().upper()
            not in TENDERS
        ):
            raise POSReturnsError(
                "tender_type must be CASH or CARD"
            )

        for name, value in {
            "captured_amount_minor": (
                self.captured_amount_minor
            ),
            "previously_refunded_minor": (
                self.previously_refunded_minor
            ),
        }.items():
            if (
                not isinstance(
                    value,
                    int,
                )
                or isinstance(
                    value,
                    bool,
                )
            ):
                raise POSReturnsError(
                    f"{name} must be an integer"
                )

        if self.captured_amount_minor <= 0:
            raise POSReturnsError(
                "captured_amount_minor must be > 0"
            )

        if self.previously_refunded_minor < 0:
            raise POSReturnsError(
                "previously_refunded_minor must be >= 0"
            )

        if not self.lines:
            raise POSReturnsError(
                "return requires at least one line"
            )

        seen = set()

        for line in self.lines:
            line.validate_basic()

            if (
                line.return_line_id
                in seen
            ):
                raise POSReturnsError(
                    "duplicate return_line_id"
                )

            seen.add(
                line.return_line_id
            )

        _iso(
            self.requested_at
        )


@dataclass(frozen=True)
class CardRefundPlan:
    return_id: str
    refund_id: str
    payment_id: str
    amount_minor: int
    currency: str
    provider_operation_plan: Any
    state: str = (
        "READY_FOR_PROVIDER_REFUND_ADAPTER"
    )


@dataclass(frozen=True)
class ProviderRefundCompletion:
    result_ref: str
    refund_id: str
    payment_id: str
    provider_id: str
    provider_reference: str
    amount_minor: int
    currency: str
    outcome: str
    completed_at: str

    def validate(self) -> None:
        if not str(
            self.result_ref
        ).startswith(
            "payment-refund-result://"
        ):
            raise POSReturnsError(
                "result_ref must use payment-refund-result://"
            )

        for name, value in {
            "refund_id": (
                self.refund_id
            ),
            "payment_id": (
                self.payment_id
            ),
            "provider_id": (
                self.provider_id
            ),
            "provider_reference": (
                self.provider_reference
            ),
            "currency": (
                self.currency
            ),
        }.items():
            _text(
                name,
                value,
            )

        if (
            not isinstance(
                self.amount_minor,
                int,
            )
            or isinstance(
                self.amount_minor,
                bool,
            )
            or self.amount_minor <= 0
        ):
            raise POSReturnsError(
                "provider refund amount_minor must be > 0"
            )

        if (
            str(
                self.outcome
            ).strip().upper()
            != "SUCCEEDED"
        ):
            raise POSReturnsError(
                "provider refund completion must be SUCCEEDED"
            )

        _iso(
            self.completed_at
        )


@dataclass(frozen=True)
class ReturnReceiptPlan:
    receipt_id: str
    return_id: str
    refund_id: str
    order_id: str
    payment_id: str
    store_id: str
    branch_id: str
    tender_type: str
    amount_minor: int
    currency: str
    lines: tuple[
        dict[
            str,
            Any,
        ],
        ...
    ]
    issued_at: str
    correlation_id: str
    state: str = (
        "READY_FOR_RETURN_RECEIPT_RENDERER_AFTER_COMMIT"
    )


@dataclass(frozen=True)
class ReturnSettlementPlan:
    settlement_id: str
    return_id: str
    refund_id: str
    payment_id: str
    refund_create: Any
    inventory_restocks: tuple[
        Any,
        ...
    ]
    payment_transition: Any | None
    receipt: ReturnReceiptPlan
    audit_event: dict[
        str,
        Any,
    ]
    transaction_requirement: str = (
        "KERNEL_ATOMIC_TRANSACTION"
    )
    event_publication: str = (
        "OUTBOX_AFTER_COMMIT"
    )
    failure_policy: str = (
        "ROLLBACK_ALL_MUTATIONS"
    )
    state: str = (
        "READY_FOR_KERNEL_RETURN_TRANSACTION_ADAPTER"
    )


@dataclass(frozen=True)
class DailySummaryQuery:
    business_date: str
    timezone_name: str
    currency: str

    def validate(
        self,
        *,
        currency_validator: Any,
    ) -> tuple[
        str,
        str,
        str,
    ]:
        try:
            business_day = (
                date.fromisoformat(
                    self.business_date
                )
            )
        except ValueError as exc:
            raise POSReturnsError(
                "business_date must be YYYY-MM-DD"
            ) from exc

        try:
            zone = ZoneInfo(
                _text(
                    "timezone_name",
                    self.timezone_name,
                )
            )
        except (
            ZoneInfoNotFoundError,
            ValueError,
        ) as exc:
            raise POSReturnsError(
                "timezone_name must be a valid IANA timezone"
            ) from exc

        start_local = datetime.combine(
            business_day,
            time.min,
            tzinfo=zone,
        )
        end_local = (
            start_local
            + timedelta(
                days=1
            )
        )

        currency = currency_validator(
            self.currency
        )

        return (
            start_local.astimezone(
                timezone.utc
            ).isoformat(),
            end_local.astimezone(
                timezone.utc
            ).isoformat(),
            currency,
        )


@dataclass(frozen=True)
class DailySummaryReadPlan:
    query_id: str
    business_date: str
    timezone_name: str
    period_start_utc: str
    period_end_utc: str
    currency: str
    tenant_context: dict[
        str,
        str,
    ]
    store_id: str
    branch_id: str
    metrics: tuple[
        str,
        ...
    ]
    sources: tuple[
        str,
        ...
    ]
    filters: dict[
        str,
        Any,
    ]
    formulas: dict[
        str,
        str,
    ]
    correlation_id: str
    state: str = (
        "READY_FOR_POS_DAILY_SUMMARY_ADAPTER"
    )


class POSReturnsReportingService:
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
        kernel_refund_type: Any,
        kernel_payment_state_type: Any,
        kernel_currency_validator: Any,
        baas_payment_service: Any,
        baas_refund_request_type: Any,
        baas_request_context_type: Any,
    ) -> None:
        self._foundation = (
            foundation
        )
        self._product_command_type = (
            product_command_type
        )
        self._staff_permission_checker = (
            staff_permission_checker
        )
        self._kernel_tenant_scope_type = (
            kernel_tenant_scope_type
        )
        self._kernel_resource_type = (
            kernel_resource_type
        )
        self._kernel_inventory_type = (
            kernel_inventory_type
        )
        self._kernel_money_type = (
            kernel_money_type
        )
        self._kernel_refund_type = (
            kernel_refund_type
        )
        self._kernel_payment_state_type = (
            kernel_payment_state_type
        )
        self._kernel_currency_validator = (
            kernel_currency_validator
        )
        self._baas_payment_service = (
            baas_payment_service
        )
        self._baas_refund_request_type = (
            baas_refund_request_type
        )
        self._baas_request_context_type = (
            baas_request_context_type
        )

        self._return_idempotency: dict[
            tuple[
                str,
                str,
                str,
            ],
            tuple[
                str,
                str,
            ],
        ] = {}

    def _validate_context(
        self,
        context: Any,
        permission: str,
    ) -> None:
        if hasattr(
            context,
            "validate",
        ):
            context.validate()

        if (
            str(
                getattr(
                    context,
                    "product",
                    "",
                )
            ).strip().upper()
            != "POS"
        ):
            raise POSReturnsError(
                "POS returns/reporting requires product=POS"
            )

        if (
            getattr(
                context,
                "store_id",
                None,
            )
            is None
            or getattr(
                context,
                "branch_id",
                None,
            )
            is None
        ):
            raise POSReturnsError(
                "POS returns/reporting requires Store + Branch context"
            )

        try:
            allowed = (
                self._staff_permission_checker(
                    context,
                    context.actor_id,
                    permission,
                )
            )
        except Exception as exc:
            raise POSReturnsError(
                f"POS staff permission check failed: {permission}"
            ) from exc

        if allowed is not True:
            raise POSReturnsError(
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

        if (
            str(
                evidence.entity_type
            ).strip().upper()
            != entity_type
        ):
            raise POSReturnsError(
                "authority evidence entity_type mismatch"
            )

        if (
            evidence.entity_id
            != entity_id
        ):
            raise POSReturnsError(
                "authority evidence entity_id mismatch"
            )

        for name in [
            "organization_id",
            "workspace_id",
            "project_id",
            "environment_id",
        ]:
            if (
                getattr(
                    evidence,
                    name,
                )
                != getattr(
                    context,
                    name,
                )
            ):
                raise POSReturnsError(
                    "cross-tenant return evidence denied"
                )

        if (
            require_status is not None
            and str(
                evidence.status or ""
            ).strip().upper()
            != require_status
        ):
            raise POSReturnsError(
                f"{entity_type} must be {require_status}"
            )

    def _tenant(
        self,
        context: Any,
    ) -> Any:
        tenant = (
            self._kernel_tenant_scope_type(
                organization_id=(
                    context.organization_id
                ),
                workspace_id=(
                    context.workspace_id
                ),
                project_id=(
                    context.project_id
                ),
                environment_id=(
                    context.environment_id
                ),
            )
        )
        tenant.validate()
        return tenant

    def _validate_request(
        self,
        *,
        context: Any,
        request: ReturnRequest,
        order_evidence: Evidence,
        payment_evidence: Evidence,
    ) -> tuple[
        int,
        str,
    ]:
        request.validate_basic()

        self._assert_evidence(
            context=context,
            evidence=order_evidence,
            entity_type="ORDER",
            entity_id=(
                request.order_id
            ),
            require_status="COMPLETED",
        )

        self._assert_evidence(
            context=context,
            evidence=payment_evidence,
            entity_type="PAYMENT",
            entity_id=(
                request.payment_id
            ),
            require_status="CAPTURED",
        )

        currency = (
            self._kernel_currency_validator(
                request.currency
            )
        )

        refund_minor = 0

        for line in request.lines:
            line_currency = (
                self._kernel_currency_validator(
                    line.currency
                )
            )

            if (
                line_currency
                != currency
            ):
                raise POSReturnsError(
                    "all return lines must use return currency"
                )

            self._assert_evidence(
                context=context,
                evidence=(
                    line.product_evidence
                ),
                entity_type="PRODUCT",
                entity_id=(
                    line.product_id
                ),
            )
            self._assert_evidence(
                context=context,
                evidence=(
                    line.variant_evidence
                ),
                entity_type=(
                    "PRODUCT_VARIANT"
                ),
                entity_id=(
                    line.product_variant_id
                ),
            )
            self._assert_evidence(
                context=context,
                evidence=(
                    line.inventory_evidence
                ),
                entity_type=(
                    "INVENTORY_ITEM"
                ),
                entity_id=(
                    line.inventory_item_id
                ),
            )

            money = (
                self._kernel_money_type(
                    amount_minor=(
                        line.unit_price_minor
                    ),
                    currency=(
                        line_currency
                    ),
                )
            )
            money.validate()

            refund_minor += (
                line.return_quantity
                * line.unit_price_minor
            )

        refund = self._kernel_refund_type(
            refund_id=(
                request.refund_id
            ),
            payment_id=(
                request.payment_id
            ),
            amount=(
                self._kernel_money_type(
                    amount_minor=(
                        refund_minor
                    ),
                    currency=currency,
                )
            ),
            reason=(
                request.reason
            ),
        )

        try:
            refund.validate(
                captured_amount=(
                    self._kernel_money_type(
                        amount_minor=(
                            request.captured_amount_minor
                        ),
                        currency=currency,
                    )
                ),
                previously_refunded_minor=(
                    request.previously_refunded_minor
                ),
            )
        except Exception as exc:
            raise POSReturnsError(
                "Kernel rejected Refund"
            ) from exc

        return (
            refund_minor,
            currency,
        )

    def plan_cash_return(
        self,
        *,
        context: Any,
        request: ReturnRequest,
        order_evidence: Evidence,
        payment_evidence: Evidence,
    ) -> dict[
        str,
        Any,
    ]:
        self._validate_context(
            context,
            "pos.return.execute",
        )

        if (
            str(
                request.tender_type
            ).strip().upper()
            != "CASH"
        ):
            raise POSReturnsError(
                "cash return requires tender_type=CASH"
            )

        refund_minor, currency = (
            self._validate_request(
                context=context,
                request=request,
                order_evidence=(
                    order_evidence
                ),
                payment_evidence=(
                    payment_evidence
                ),
            )
        )

        settlement_id, created = (
            self._claim_return_idempotency(
                context=context,
                request=request,
                refund_minor=(
                    refund_minor
                ),
            )
        )

        plan = self._finalize_return(
            context=context,
            request=request,
            refund_minor=(
                refund_minor
            ),
            currency=currency,
            settlement_id=(
                settlement_id
            ),
            provider_reference=(
                f"cash-refund://{settlement_id}"
            ),
            completed_at=(
                _iso(
                    request.requested_at
                )
            ),
        )

        return {
            "created": created,
            "plan": plan,
        }

    def plan_card_return(
        self,
        *,
        context: Any,
        request: ReturnRequest,
        order_evidence: Evidence,
        payment_evidence: Evidence,
        provider_id: str,
        provider_reference: str,
    ) -> dict[
        str,
        Any,
    ]:
        self._validate_context(
            context,
            "pos.return.execute",
        )

        if (
            str(
                request.tender_type
            ).strip().upper()
            != "CARD"
        ):
            raise POSReturnsError(
                "card return requires tender_type=CARD"
            )

        refund_minor, currency = (
            self._validate_request(
                context=context,
                request=request,
                order_evidence=(
                    order_evidence
                ),
                payment_evidence=(
                    payment_evidence
                ),
            )
        )

        settlement_id, created = (
            self._claim_return_idempotency(
                context=context,
                request=request,
                refund_minor=(
                    refund_minor
                ),
            )
        )

        baas_context = (
            self._baas_context(
                context=context,
                operation=(
                    "pos.return.card.plan"
                ),
                idempotency_key=(
                    request.idempotency_key
                ),
            )
        )

        refund_request = (
            self._baas_refund_request_type(
                refund_id=(
                    request.refund_id
                ),
                payment_id=(
                    request.payment_id
                ),
                amount_minor=(
                    refund_minor
                ),
                currency=currency,
                reason=(
                    request.reason
                ),
                idempotency_key=(
                    request.idempotency_key
                ),
                requested_at=(
                    _iso(
                        request.requested_at
                    )
                ),
            )
        )

        result = (
            self._baas_payment_service.create_refund_plan(
                provider_id=(
                    _text(
                        "provider_id",
                        provider_id,
                    )
                ),
                provider_reference=(
                    _text(
                        "provider_reference",
                        provider_reference,
                    )
                ),
                request=(
                    refund_request
                ),
                kernel_current_status=(
                    "CAPTURED"
                ),
                captured_amount_minor=(
                    request.captured_amount_minor
                ),
                previously_refunded_minor=(
                    request.previously_refunded_minor
                ),
                request_context=(
                    baas_context
                ),
            )
        )

        provider_plan = result[
            "plan"
        ]

        return {
            "created": created,
            "settlement_id": (
                settlement_id
            ),
            "plan": CardRefundPlan(
                return_id=(
                    request.return_id
                ),
                refund_id=(
                    request.refund_id
                ),
                payment_id=(
                    request.payment_id
                ),
                amount_minor=(
                    refund_minor
                ),
                currency=currency,
                provider_operation_plan=(
                    provider_plan
                ),
            ),
        }

    def complete_card_return(
        self,
        *,
        context: Any,
        request: ReturnRequest,
        card_plan: CardRefundPlan,
        completion: ProviderRefundCompletion,
    ) -> ReturnSettlementPlan:
        self._validate_context(
            context,
            "pos.return.execute",
        )

        completion.validate()

        provider_plan = (
            card_plan.provider_operation_plan
        )

        checks = {
            "return_id": (
                card_plan.return_id
                == request.return_id
            ),
            "refund_id": (
                completion.refund_id
                == card_plan.refund_id
                == provider_plan.refund_id
            ),
            "payment_id": (
                completion.payment_id
                == card_plan.payment_id
                == provider_plan.payment_id
            ),
            "provider_id": (
                completion.provider_id
                == provider_plan.provider_id
            ),
            "provider_reference": (
                completion.provider_reference
                == provider_plan.provider_reference
            ),
            "amount_minor": (
                completion.amount_minor
                == card_plan.amount_minor
                == provider_plan.amount_minor
            ),
            "currency": (
                completion.currency
                == card_plan.currency
                == provider_plan.currency
            ),
        }

        if not all(
            checks.values()
        ):
            raise POSReturnsError(
                "card refund completion does not match approved BaaS plan"
            )

        refund_minor, currency = (
            self._validate_request(
                context=context,
                request=request,
                order_evidence=Evidence(
                    source="kernel.commerce",
                    entity_type="ORDER",
                    entity_id=(
                        request.order_id
                    ),
                    organization_id=(
                        context.organization_id
                    ),
                    workspace_id=(
                        context.workspace_id
                    ),
                    project_id=(
                        context.project_id
                    ),
                    environment_id=(
                        context.environment_id
                    ),
                    snapshot_ref=(
                        "kernel-snapshot://return-completion/order"
                    ),
                    status="COMPLETED",
                ),
                payment_evidence=Evidence(
                    source="kernel.commerce",
                    entity_type="PAYMENT",
                    entity_id=(
                        request.payment_id
                    ),
                    organization_id=(
                        context.organization_id
                    ),
                    workspace_id=(
                        context.workspace_id
                    ),
                    project_id=(
                        context.project_id
                    ),
                    environment_id=(
                        context.environment_id
                    ),
                    snapshot_ref=(
                        "kernel-snapshot://return-completion/payment"
                    ),
                    status="CAPTURED",
                ),
            )
        )

        settlement_id = (
            "pos_card_return_"
            + sha256(
                completion.result_ref.encode(
                    "utf-8"
                )
            ).hexdigest()[:24]
        )

        return self._finalize_return(
            context=context,
            request=request,
            refund_minor=(
                refund_minor
            ),
            currency=currency,
            settlement_id=(
                settlement_id
            ),
            provider_reference=(
                completion.provider_reference
            ),
            completed_at=(
                _iso(
                    completion.completed_at
                )
            ),
        )

    def _finalize_return(
        self,
        *,
        context: Any,
        request: ReturnRequest,
        refund_minor: int,
        currency: str,
        settlement_id: str,
        provider_reference: str,
        completed_at: str,
    ) -> ReturnSettlementPlan:
        refund_create = (
            self._foundation.plan(
                self._product_command_type(
                    action="CREATE",
                    entity_type="REFUND",
                    entity_id=(
                        request.refund_id
                    ),
                    context=context,
                    idempotency_key=(
                        f"{request.idempotency_key}:refund"
                    ),
                    input_metadata={
                        "payment_id": (
                            request.payment_id
                        ),
                        "order_id": (
                            request.order_id
                        ),
                        "amount_minor": (
                            refund_minor
                        ),
                        "currency": (
                            currency
                        ),
                        "reason": (
                            request.reason
                        ),
                        "provider_reference": (
                            provider_reference
                        ),
                        "requested_at": (
                            completed_at
                        ),
                    },
                )
            )["plan"]
        )

        restocks = []

        for line in request.lines:
            target_on_hand = (
                line.current_quantity_on_hand
                + line.return_quantity
            )
            target_reserved = (
                line.current_quantity_reserved
            )

            resource = (
                self._kernel_resource_type(
                    id=(
                        line.inventory_item_id
                    ),
                    entity_type=(
                        "INVENTORY_ITEM"
                    ),
                    tenant=(
                        self._tenant(
                            context
                        )
                    ),
                    created_at=(
                        completed_at
                    ),
                    updated_at=(
                        completed_at
                    ),
                )
            )

            item = (
                self._kernel_inventory_type(
                    resource=resource,
                    product_variant_id=(
                        line.product_variant_id
                    ),
                    store_id=(
                        context.store_id
                    ),
                    branch_id=(
                        context.branch_id
                    ),
                    quantity_on_hand=(
                        target_on_hand
                    ),
                    quantity_reserved=(
                        target_reserved
                    ),
                )
            )

            try:
                item.validate()
            except Exception as exc:
                raise POSReturnsError(
                    "Kernel rejected return inventory restock"
                ) from exc

            restocks.append(
                self._foundation.plan(
                    self._product_command_type(
                        action="UPDATE",
                        entity_type=(
                            "INVENTORY_ITEM"
                        ),
                        entity_id=(
                            line.inventory_item_id
                        ),
                        context=context,
                        idempotency_key=(
                            f"{request.idempotency_key}:restock:"
                            f"{line.inventory_item_id}"
                        ),
                        input_metadata={
                            "expected_quantity_on_hand": (
                                line.current_quantity_on_hand
                            ),
                            "expected_quantity_reserved": (
                                line.current_quantity_reserved
                            ),
                            "target_quantity_on_hand": (
                                target_on_hand
                            ),
                            "target_quantity_reserved": (
                                target_reserved
                            ),
                            "quantity_on_hand_delta": (
                                line.return_quantity
                            ),
                            "quantity_reserved_delta": 0,
                            "reason": (
                                "POS_RETURN_RESTOCK"
                            ),
                            "source_ref": (
                                f"pos-return://{request.return_id}"
                            ),
                            "persistence_requirement": (
                                "ATOMIC_COMPARE_EXPECTED_AND_UPDATE"
                            ),
                            "requested_at": (
                                completed_at
                            ),
                        },
                    )
                )["plan"]
            )

        cumulative = (
            request.previously_refunded_minor
            + refund_minor
        )
        payment_transition = None

        if (
            cumulative
            == request.captured_amount_minor
        ):
            try:
                target = (
                    self._kernel_payment_state_type(
                        payment_id=(
                            request.payment_id
                        ),
                        order_id=(
                            request.order_id
                        ),
                        status="CAPTURED",
                        amount=(
                            self._kernel_money_type(
                                amount_minor=(
                                    request.captured_amount_minor
                                ),
                                currency=currency,
                            )
                        ),
                    ).transition(
                        "REFUNDED"
                    )
                )
            except Exception as exc:
                raise POSReturnsError(
                    "Kernel rejected full-refund Payment transition"
                ) from exc

            payment_transition = (
                self._foundation.plan(
                    self._product_command_type(
                        action="TRANSITION",
                        entity_type="PAYMENT",
                        entity_id=(
                            request.payment_id
                        ),
                        context=context,
                        idempotency_key=(
                            f"{request.idempotency_key}:payment-refunded"
                        ),
                        input_metadata={
                            "from_status": (
                                "CAPTURED"
                            ),
                            "to_status": (
                                target.status
                            ),
                            "refund_id": (
                                request.refund_id
                            ),
                            "cumulative_refunded_minor": (
                                cumulative
                            ),
                            "requested_at": (
                                completed_at
                            ),
                        },
                    )
                )["plan"]
            )

        receipt_lines = tuple(
            {
                "order_item_id": (
                    line.order_item_id
                ),
                "product_id": (
                    line.product_id
                ),
                "product_variant_id": (
                    line.product_variant_id
                ),
                "return_quantity": (
                    line.return_quantity
                ),
                "unit_price_minor": (
                    line.unit_price_minor
                ),
                "refund_minor": (
                    line.return_quantity
                    * line.unit_price_minor
                ),
                "currency": currency,
            }
            for line in request.lines
        )

        receipt = ReturnReceiptPlan(
            receipt_id=(
                "return_receipt_"
                + sha256(
                    _canonical({
                        "return_id": (
                            request.return_id
                        ),
                        "refund_id": (
                            request.refund_id
                        ),
                        "payment_id": (
                            request.payment_id
                        ),
                        "amount_minor": (
                            refund_minor
                        ),
                        "currency": (
                            currency
                        ),
                    }).encode(
                        "utf-8"
                    )
                ).hexdigest()[:24]
            ),
            return_id=(
                request.return_id
            ),
            refund_id=(
                request.refund_id
            ),
            order_id=(
                request.order_id
            ),
            payment_id=(
                request.payment_id
            ),
            store_id=(
                context.store_id
            ),
            branch_id=(
                context.branch_id
            ),
            tender_type=(
                str(
                    request.tender_type
                ).strip().upper()
            ),
            amount_minor=(
                refund_minor
            ),
            currency=currency,
            lines=receipt_lines,
            issued_at=(
                completed_at
            ),
            correlation_id=(
                context.correlation_id
            ),
        )

        audit_event = {
            "event_type": (
                "pos.return.completed"
            ),
            "return_id": (
                request.return_id
            ),
            "refund_id": (
                request.refund_id
            ),
            "order_id": (
                request.order_id
            ),
            "payment_id": (
                request.payment_id
            ),
            "store_id": (
                context.store_id
            ),
            "branch_id": (
                context.branch_id
            ),
            "amount_minor": (
                refund_minor
            ),
            "currency": (
                currency
            ),
            "tender_type": (
                str(
                    request.tender_type
                ).strip().upper()
            ),
            "correlation_id": (
                context.correlation_id
            ),
        }

        return ReturnSettlementPlan(
            settlement_id=(
                settlement_id
            ),
            return_id=(
                request.return_id
            ),
            refund_id=(
                request.refund_id
            ),
            payment_id=(
                request.payment_id
            ),
            refund_create=(
                refund_create
            ),
            inventory_restocks=(
                tuple(
                    restocks
                )
            ),
            payment_transition=(
                payment_transition
            ),
            receipt=receipt,
            audit_event=(
                audit_event
            ),
        )

    def _claim_return_idempotency(
        self,
        *,
        context: Any,
        request: ReturnRequest,
        refund_minor: int,
    ) -> tuple[
        str,
        bool,
    ]:
        material = {
            "return_id": (
                request.return_id
            ),
            "refund_id": (
                request.refund_id
            ),
            "order_id": (
                request.order_id
            ),
            "payment_id": (
                request.payment_id
            ),
            "tender_type": (
                str(
                    request.tender_type
                ).strip().upper()
            ),
            "refund_minor": (
                refund_minor
            ),
            "currency": (
                request.currency
            ),
            "lines": [
                {
                    "return_line_id": (
                        line.return_line_id
                    ),
                    "order_item_id": (
                        line.order_item_id
                    ),
                    "return_quantity": (
                        line.return_quantity
                    ),
                    "unit_price_minor": (
                        line.unit_price_minor
                    ),
                }
                for line in request.lines
            ],
        }

        fingerprint = sha256(
            _canonical(
                material
            ).encode(
                "utf-8"
            )
        ).hexdigest()

        scope = (
            context.organization_id,
            context.environment_id,
            request.idempotency_key,
        )

        existing = (
            self._return_idempotency.get(
                scope
            )
        )

        if existing is not None:
            old_hash, settlement_id = (
                existing
            )

            if old_hash != fingerprint:
                raise POSReturnsError(
                    "return idempotency key reused with different material"
                )

            return (
                settlement_id,
                False,
            )

        settlement_id = (
            "pos_return_"
            + sha256(
                _canonical({
                    "scope": scope,
                    "fingerprint": (
                        fingerprint
                    ),
                }).encode(
                    "utf-8"
                )
            ).hexdigest()[:24]
        )

        self._return_idempotency[
            scope
        ] = (
            fingerprint,
            settlement_id,
        )

        return (
            settlement_id,
            True,
        )

    def plan_daily_summary(
        self,
        *,
        context: Any,
        query: DailySummaryQuery,
    ) -> DailySummaryReadPlan:
        self._validate_context(
            context,
            "pos.summary.read",
        )

        (
            period_start,
            period_end,
            currency,
        ) = query.validate(
            currency_validator=(
                self._kernel_currency_validator
            )
        )

        material = {
            "organization_id": (
                context.organization_id
            ),
            "workspace_id": (
                context.workspace_id
            ),
            "project_id": (
                context.project_id
            ),
            "environment_id": (
                context.environment_id
            ),
            "store_id": (
                context.store_id
            ),
            "branch_id": (
                context.branch_id
            ),
            "business_date": (
                query.business_date
            ),
            "timezone_name": (
                query.timezone_name
            ),
            "period_start_utc": (
                period_start
            ),
            "period_end_utc": (
                period_end
            ),
            "currency": (
                currency
            ),
        }

        return DailySummaryReadPlan(
            query_id=(
                "pos_daily_summary_"
                + sha256(
                    _canonical(
                        material
                    ).encode(
                        "utf-8"
                    )
                ).hexdigest()[:24]
            ),
            business_date=(
                query.business_date
            ),
            timezone_name=(
                query.timezone_name
            ),
            period_start_utc=(
                period_start
            ),
            period_end_utc=(
                period_end
            ),
            currency=currency,
            tenant_context={
                "organization_id": (
                    context.organization_id
                ),
                "workspace_id": (
                    context.workspace_id
                ),
                "project_id": (
                    context.project_id
                ),
                "environment_id": (
                    context.environment_id
                ),
            },
            store_id=(
                context.store_id
            ),
            branch_id=(
                context.branch_id
            ),
            metrics=(
                SUMMARY_METRICS
            ),
            sources=(
                "kernel.orders",
                "kernel.order_items",
                "kernel.payments",
                "kernel.refunds",
                "kernel.inventory_items",
                "kernel.audit",
            ),
            filters={
                "store_id": (
                    context.store_id
                ),
                "branch_id": (
                    context.branch_id
                ),
                "currency": (
                    currency
                ),
                "period_start_utc": (
                    period_start
                ),
                "period_end_utc": (
                    period_end
                ),
                "order_status": (
                    "COMPLETED"
                ),
            },
            formulas={
                "gross_sales_minor": (
                    "sum(captured/completed sale totals)"
                ),
                "refund_minor": (
                    "sum(refund amount_minor)"
                ),
                "net_sales_minor": (
                    "gross_sales_minor - refund_minor"
                ),
                "items_sold": (
                    "sum(completed order item quantities)"
                ),
                "items_returned": (
                    "sum(returned quantities linked to refunds)"
                ),
            },
            correlation_id=(
                context.correlation_id
            ),
        )

    def _baas_context(
        self,
        *,
        context: Any,
        operation: str,
        idempotency_key: str,
    ) -> Any:
        return (
            self._baas_request_context_type(
                request_id=(
                    "req_pos_return_"
                    + sha256(
                        (
                            f"{context.correlation_id}"
                            f"\x1f{operation}"
                            f"\x1f{idempotency_key}"
                        ).encode(
                            "utf-8"
                        )
                    ).hexdigest()[:20]
                ),
                correlation_id=(
                    context.correlation_id
                ),
                service="payments",
                operation=operation,
                organization_id=(
                    context.organization_id
                ),
                workspace_id=(
                    context.workspace_id
                ),
                project_id=(
                    context.project_id
                ),
                environment_id=(
                    context.environment_id
                ),
                actor_id=(
                    context.actor_id
                ),
                actor_type=(
                    context.actor_type
                ),
                kernel_authorization_ref=(
                    context.kernel_authorization_ref
                ),
                idempotency_key=(
                    idempotency_key
                ),
            )
        )
