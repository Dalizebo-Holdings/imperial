from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kernel.crm.runtime import (
    Activity,
    PipelineStage,
    Deal,
    CRMPrimitiveError,
    Money,
    TenantScope,
    CRMResource,
)


class CRMSError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise CRMSError(f"{name} must not be empty")
    result = str(value).strip()
    if not result:
        raise CRMSError(f"{name} must not be empty")
    return result


def _time(value: str | None = None) -> str:
    from datetime import datetime, timezone
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CRMSError("requested_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise CRMSError("requested_at must be timezone-aware")
    return parsed.isoformat()


def _validate_context(context: Any) -> None:
    if hasattr(context, "validate"):
        context.validate()


@dataclass(frozen=True)
class ActivityCreateRequest:
    activity_id: str
    subject: str
    activity_type: str
    due_at: str | None = None
    completed_at: str | None = None
    related_to_entity_type: str | None = None
    related_to_entity_id: str | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("activity_id", self.activity_id)
        _text("idempotency_key", self.idempotency_key)
        _text("subject", self.subject)
        _text("activity_type", self.activity_type)

        due_at = self.due_at
        if due_at is not None:
            try:
                datetime.fromisoformat(due_at)
            except ValueError:
                raise CRMSError("due_at must be ISO-8601")

        completed_at = self.completed_at
        if completed_at is not None:
            try:
                datetime.fromisoformat(completed_at)
            except ValueError:
                raise CRMSError("completed_at must be ISO-8601")

        return {
            "activity_id": self.activity_id,
            "subject": self.subject,
            "activity_type": self.activity_type,
            "due_at": due_at,
            "completed_at": self.completed_at,
            "related_to_entity_type": self.related_to_entity_type,
            "related_to_entity_id": self.related_to_entity_id,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class PipelineStageCreateRequest:
    pipeline_stage_id: str
    name: str
    probability: int
    order: int
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("pipeline_stage_id", self.pipeline_stage_id)
        _text("idempotency_key", self.idempotency_key)
        _text("name", self.name)
        if not (0 <= self.probability <= 100):
            raise CRMSError("probability must be between 0 and 100")
        if not isinstance(self.order, int):
            raise CRMSError("order must be an integer")
        return {
            "pipeline_stage_id": self.pipeline_stage_id,
            "name": self.name,
            "probability": self.probability,
            "order": self.order,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class DealCreateRequest:
    deal_id: str
    pipeline_stage_id: str
    amount: dict[str, Any] | None = None  # Expecting {amount_minor: int, currency: str}
    expected_close_at: str | None = None
    related_to_entity_type: str | None = None
    related_to_entity_id: str | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("deal_id", self.deal_id)
        _text("idempotency_key", self.idempotency_key)
        _text("pipeline_stage_id", self.pipeline_stage_id)

        amount = None
        if self.amount is not None:
            if not isinstance(self.amount, dict):
                raise CRMSError("amount must be a dict with amount_minor and currency")
            amount_minor = self.amount.get("amount_minor")
            currency = self.amount.get("currency")
            if not isinstance(amount_minor, int):
                raise CRMSError("amount_minor must be an integer")
            if not isinstance(currency, str):
                raise CRMSError("currency must be a string")
            # Validate currency format (three uppercase letters)
            import re
            if not re.fullmatch(r"[A-Z]{3}", currency):
                raise CRMSError("currency must be three uppercase letters")
            amount = {"amount_minor": amount_minor, "currency": currency}

        expected_close_at = self.expected_close_at
        if expected_close_at is not None:
            try:
                datetime.fromisoformat(expected_close_at)
            except ValueError:
                raise CRMSError("expected_close_at must be ISO-8601")

        return {
            "deal_id": self.deal_id,
            "pipeline_stage_id": self.pipeline_stage_id,
            "amount": amount,
            "expected_close_at": expected_close_at,
            "related_to_entity_type": self.related_to_entity_type,
            "related_to_entity_id": self.related_to_entity_id,
            "requested_at": _time(self.requested_at),
        }


class CRMSService:
    def __init__(
        self,
        *,
        foundation: Any,
        product_command_type: Any,
    ) -> None:
        self._foundation = foundation
        self._product_command_type = product_command_type

    def plan_create_activity(
        self,
        *,
        context: Any,
        request: ActivityCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="ACTIVITY",
                entity_id=request.activity_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "CRM_ACTIVITY",
                },
            )
        )

    def plan_create_pipeline_stage(
        self,
        *,
        context: Any,
        request: PipelineStageCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="PIPELINE_STAGE",
                entity_id=request.pipeline_stage_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "CRM_PIPELINE_STAGE",
                },
            )
        )

    def plan_create_deal(
        self,
        *,
        context: Any,
        request: DealCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="DEAL",
                entity_id=request.deal_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "CRM_DEAL",
                },
            )
        )

    # We can add update and other methods as needed.