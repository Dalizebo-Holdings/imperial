from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any


class CommerceRefundError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise CommerceRefundError(
            f"{name} must not be empty"
        )
    result = str(value).strip()
    if not result:
        raise CommerceRefundError(
            f"{name} must not be empty"
        )
    return result


def _time(value: str | None = None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CommerceRefundError(
            "timestamp must be ISO-8601"
        ) from exc
    if parsed.tzinfo is None:
        raise CommerceRefundError(
            "timestamp must be timezone-aware"
        )
    return parsed.isoformat()


@dataclass(frozen=True)
class CommerceRefundEvidence:
    source: str
    entity_type: str
    entity_id: str
    organization_id: str
    workspace_id: str
    project_id: str
    environment_id: str
    status: str

    def validate(self) -> None:
        if str(self.source).strip() != "kernel.commerce":
            raise CommerceRefundError(
                "refund evidence must come from kernel.commerce"
            )
        for name, value in self.__dict__.items():
            _text(name, value)


@dataclass(frozen=True)
class CommerceRefundRequest:
    refund_id: str
    order_id: str
    payment_id: str
    amount_minor: int
    captured_amount_minor: int
    previously_refunded_minor: int
    currency: str
    reason: str
    provider_id: str
    provider_reference: str
    idempotency_key: str
    requested_at: str

    def validate_basic(self) -> None:
        for name, value in {
            "refund_id": self.refund_id,
            "order_id": self.order_id,
            "payment_id": self.payment_id,
            "currency": self.currency,
            "reason": self.reason,
            "provider_id": self.provider_id,
            "provider_reference": self.provider_reference,
            "idempotency_key": self.idempotency_key,
        }.items():
            _text(name, value)

        for name, value in {
            "amount_minor": self.amount_minor,
            "captured_amount_minor": self.captured_amount_minor,
            "previously_refunded_minor": self.previously_refunded_minor,
        }.items():
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
            ):
                raise CommerceRefundError(
                    f"{name} must be an integer"
                )

        if self.amount_minor <= 0:
            raise CommerceRefundError(
                "amount_minor must be > 0"
            )

        if self.captured_amount_minor <= 0:
            raise CommerceRefundError(
                "captured_amount_minor must be > 0"
            )

        if self.previously_refunded_minor < 0:
            raise CommerceRefundError(
                "previously_refunded_minor must be >= 0"
            )

        _time(self.requested_at)


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
        if not str(self.result_ref).startswith(
            "payment-refund-result://"
        ):
            raise CommerceRefundError(
                "result_ref must use payment-refund-result://"
            )

        for name, value in {
            "refund_id": self.refund_id,
            "payment_id": self.payment_id,
            "provider_id": self.provider_id,
            "provider_reference": self.provider_reference,
            "currency": self.currency,
        }.items():
            _text(name, value)

        if (
            not isinstance(self.amount_minor, int)
            or isinstance(self.amount_minor, bool)
            or self.amount_minor <= 0
        ):
            raise CommerceRefundError(
                "completion amount_minor must be > 0"
            )

        if str(self.outcome).strip().upper() != "SUCCEEDED":
            raise CommerceRefundError(
                "refund completion must be SUCCEEDED"
            )

        _time(self.completed_at)


@dataclass(frozen=True)
class CommerceProviderRefundPlan:
    refund_id: str
    order_id: str
    payment_id: str
    amount_minor: int
    currency: str
    provider_operation_plan: Any
    created: bool
    state: str = "READY_FOR_PROVIDER_REFUND_ADAPTER"


@dataclass(frozen=True)
class CommerceRefundSettlementPlan:
    refund_id: str
    order_id: str
    payment_id: str
    refund_create: Any
    payment_transition: Any | None
    audit_event: dict[str, Any]
    provider_result_ref: str
    state: str = "READY_FOR_KERNEL_REFUND_TRANSACTION_ADAPTER"


class CommerceRefundService:
    def __init__(
        self,
        *,
        foundation: Any,
        product_command_type: Any,
        kernel_money_type: Any,
        kernel_refund_type: Any,
        kernel_payment_state_type: Any,
        kernel_currency_validator: Any,
        baas_payment_service: Any,
        baas_refund_request_type: Any,
        baas_request_context_type: Any,
    ) -> None:
        self._foundation = foundation
        self._product_command_type = product_command_type
        self._kernel_money_type = kernel_money_type
        self._kernel_refund_type = kernel_refund_type
        self._kernel_payment_state_type = kernel_payment_state_type
        self._kernel_currency_validator = kernel_currency_validator
        self._payment_service = baas_payment_service
        self._refund_request_type = baas_refund_request_type
        self._request_context_type = baas_request_context_type

    @staticmethod
    def _validate_context(context: Any) -> None:
        if hasattr(context, "validate"):
            context.validate()

        if (
            str(getattr(context, "product", "")).strip().upper()
            != "COMMERCE"
        ):
            raise CommerceRefundError(
                "Commerce Refunds requires product=COMMERCE"
            )

        if getattr(context, "store_id", None) is None:
            raise CommerceRefundError(
                "Commerce Refunds requires Store context"
            )

    @staticmethod
    def _assert_evidence(
        *,
        context: Any,
        evidence: CommerceRefundEvidence,
        entity_type: str,
        entity_id: str,
        allowed_statuses: set[str],
    ) -> None:
        evidence.validate()

        if str(evidence.entity_type).strip().upper() != entity_type:
            raise CommerceRefundError(
                "refund evidence entity_type mismatch"
            )

        if evidence.entity_id != entity_id:
            raise CommerceRefundError(
                "refund evidence entity_id mismatch"
            )

        for name in [
            "organization_id",
            "workspace_id",
            "project_id",
            "environment_id",
        ]:
            if getattr(evidence, name) != getattr(context, name):
                raise CommerceRefundError(
                    "cross-tenant refund evidence denied"
                )

        if str(evidence.status).strip().upper() not in allowed_statuses:
            raise CommerceRefundError(
                f"{entity_type} status is not refund-eligible"
            )

    def _baas_context(
        self,
        *,
        context: Any,
        operation: str,
        idempotency_key: str,
    ) -> Any:
        return self._request_context_type(
            request_id=(
                "req_commerce_refund_"
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

    def plan_provider_refund(
        self,
        *,
        context: Any,
        request: CommerceRefundRequest,
        order_evidence: CommerceRefundEvidence,
        payment_evidence: CommerceRefundEvidence,
    ) -> CommerceProviderRefundPlan:
        self._validate_context(context)
        request.validate_basic()

        self._assert_evidence(
            context=context,
            evidence=order_evidence,
            entity_type="ORDER",
            entity_id=request.order_id,
            allowed_statuses={"CONFIRMED", "COMPLETED"},
        )
        self._assert_evidence(
            context=context,
            evidence=payment_evidence,
            entity_type="PAYMENT",
            entity_id=request.payment_id,
            allowed_statuses={"CAPTURED"},
        )

        currency = self._kernel_currency_validator(
            request.currency
        )

        refund = self._kernel_refund_type(
            refund_id=request.refund_id,
            payment_id=request.payment_id,
            amount=self._kernel_money_type(
                amount_minor=request.amount_minor,
                currency=currency,
            ),
            reason=request.reason,
        )

        try:
            refund.validate(
                captured_amount=self._kernel_money_type(
                    amount_minor=request.captured_amount_minor,
                    currency=currency,
                ),
                previously_refunded_minor=request.previously_refunded_minor,
            )
        except Exception as exc:
            raise CommerceRefundError(
                "Kernel rejected Commerce refund"
            ) from exc

        baas_request = self._refund_request_type(
            refund_id=request.refund_id,
            payment_id=request.payment_id,
            amount_minor=request.amount_minor,
            currency=currency,
            reason=request.reason,
            idempotency_key=request.idempotency_key,
            requested_at=_time(request.requested_at),
        )

        result = self._payment_service.create_refund_plan(
            provider_id=request.provider_id,
            provider_reference=request.provider_reference,
            request=baas_request,
            kernel_current_status="CAPTURED",
            captured_amount_minor=request.captured_amount_minor,
            previously_refunded_minor=request.previously_refunded_minor,
            request_context=self._baas_context(
                context=context,
                operation="commerce.refund.plan",
                idempotency_key=request.idempotency_key,
            ),
        )

        provider_plan = result["plan"]

        return CommerceProviderRefundPlan(
            refund_id=request.refund_id,
            order_id=request.order_id,
            payment_id=request.payment_id,
            amount_minor=request.amount_minor,
            currency=currency,
            provider_operation_plan=provider_plan,
            created=bool(result["created"]),
        )

    def complete_provider_refund(
        self,
        *,
        context: Any,
        request: CommerceRefundRequest,
        approved_plan: CommerceProviderRefundPlan,
        completion: ProviderRefundCompletion,
        order_evidence: CommerceRefundEvidence,
        payment_evidence: CommerceRefundEvidence,
    ) -> CommerceRefundSettlementPlan:
        self._validate_context(context)
        request.validate_basic()
        completion.validate()

        self._assert_evidence(
            context=context,
            evidence=order_evidence,
            entity_type="ORDER",
            entity_id=request.order_id,
            allowed_statuses={"CONFIRMED", "COMPLETED"},
        )
        self._assert_evidence(
            context=context,
            evidence=payment_evidence,
            entity_type="PAYMENT",
            entity_id=request.payment_id,
            allowed_statuses={"CAPTURED"},
        )

        provider_plan = approved_plan.provider_operation_plan

        checks = {
            "refund_id": (
                completion.refund_id
                == request.refund_id
                == approved_plan.refund_id
                == provider_plan.refund_id
            ),
            "payment_id": (
                completion.payment_id
                == request.payment_id
                == approved_plan.payment_id
                == provider_plan.payment_id
            ),
            "provider_id": (
                completion.provider_id
                == request.provider_id
                == provider_plan.provider_id
            ),
            "provider_reference": (
                completion.provider_reference
                == request.provider_reference
                == provider_plan.provider_reference
            ),
            "amount_minor": (
                completion.amount_minor
                == request.amount_minor
                == approved_plan.amount_minor
                == provider_plan.amount_minor
            ),
            "currency": (
                completion.currency
                == approved_plan.currency
                == provider_plan.currency
            ),
        }

        if not all(checks.values()):
            raise CommerceRefundError(
                "provider completion does not match approved Commerce refund"
            )

        currency = self._kernel_currency_validator(
            request.currency
        )
        completed_at = _time(
            completion.completed_at
        )

        refund_create = self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="REFUND",
                entity_id=request.refund_id,
                context=context,
                idempotency_key=(
                    f"{request.idempotency_key}:refund-record"
                ),
                input_metadata={
                    "order_id": request.order_id,
                    "payment_id": request.payment_id,
                    "amount_minor": request.amount_minor,
                    "currency": currency,
                    "reason": request.reason,
                    "provider_id": request.provider_id,
                    "provider_reference": request.provider_reference,
                    "provider_result_ref": completion.result_ref,
                    "requested_at": completed_at,
                },
            )
        )["plan"]

        payment_transition = None
        cumulative = (
            request.previously_refunded_minor
            + request.amount_minor
        )

        if cumulative == request.captured_amount_minor:
            try:
                refunded = self._kernel_payment_state_type(
                    payment_id=request.payment_id,
                    order_id=request.order_id,
                    status="CAPTURED",
                    amount=self._kernel_money_type(
                        amount_minor=request.captured_amount_minor,
                        currency=currency,
                    ),
                ).transition("REFUNDED")
            except Exception as exc:
                raise CommerceRefundError(
                    "Kernel rejected full-refund Payment transition"
                ) from exc

            payment_transition = self._foundation.plan(
                self._product_command_type(
                    action="TRANSITION",
                    entity_type="PAYMENT",
                    entity_id=request.payment_id,
                    context=context,
                    idempotency_key=(
                        f"{request.idempotency_key}:payment-refunded"
                    ),
                    input_metadata={
                        "from_status": "CAPTURED",
                        "to_status": refunded.status,
                        "refund_id": request.refund_id,
                        "cumulative_refunded_minor": cumulative,
                        "requested_at": completed_at,
                    },
                )
            )["plan"]

        audit_event = {
            "event_type": "commerce.refund.completed",
            "refund_id": request.refund_id,
            "order_id": request.order_id,
            "payment_id": request.payment_id,
            "provider_id": request.provider_id,
            "provider_reference": request.provider_reference,
            "amount_minor": request.amount_minor,
            "currency": currency,
            "organization_id": context.organization_id,
            "store_id": context.store_id,
            "correlation_id": context.correlation_id,
            "provider_result_ref": completion.result_ref,
        }

        return CommerceRefundSettlementPlan(
            refund_id=request.refund_id,
            order_id=request.order_id,
            payment_id=request.payment_id,
            refund_create=refund_create,
            payment_transition=payment_transition,
            audit_event=audit_event,
            provider_result_ref=completion.result_ref,
        )
