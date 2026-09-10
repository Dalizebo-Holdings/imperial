from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Any


class CRMPrimitiveError(ValueError):
    pass


def _require_text(name: str, value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise CRMPrimitiveError(
            f"{name} must not be empty"
        )
    return normalized


def validate_currency(currency: str) -> str:
    value = str(currency).strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", value):
        raise CRMPrimitiveError(
            "currency must be three uppercase letters"
        )
    return value


@dataclass(frozen=True)
class Money:
    amount_minor: int
    currency: str

    def validate(self, *, allow_negative: bool = False) -> None:
        if not isinstance(self.amount_minor, int):
            raise CRMPrimitiveError(
                "amount_minor must be an integer"
            )
        if not allow_negative and self.amount_minor < 0:
            raise CRMPrimitiveError(
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
class CRMResource:
    id: str
    entity_type: str
    tenant: TenantScope
    created_at: str
    updated_at: str

    def validate(self) -> None:
        _require_text("id", self.id)

        if self.entity_type not in CRM_ENTITY_TYPES:
            raise CRMPrimitiveError(
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
                raise CRMPrimitiveError(
                    f"{name} must be ISO-8601"
                ) from exc


# Entity types for CRM
CRM_ENTITY_TYPES = {
    "ACTIVITY",
    "PIPELINE_STAGE",
    "DEAL",
    "CAMPAIGN",
    "SEGMENT",
    "REPORT",
}


@dataclass(frozen=True)
class Activity:
    resource: CRMResource
    subject: str
    activity_type: str  # e.g., CALL, MEETING, EMAIL, NOTE
    due_at: str | None = None
    completed_at: str | None = None
    related_to_entity_type: str | None = None  # e.g., CUSTOMER, DEAL
    related_to_entity_id: str | None = None

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "ACTIVITY":
            raise CRMPrimitiveError(
                "resource entity_type must be ACTIVITY"
            )
        _require_text("subject", self.subject)
        _require_text("activity_type", self.activity_type)
        # Validate activity_type against allowed list? For now, free string.
        if self.due_at is not None:
            try:
                datetime.fromisoformat(self.due_at)
            except ValueError as exc:
                raise CRMPrimitiveError(
                    "due_at must be ISO-8601"
                ) from exc
        if self.completed_at is not None:
            try:
                datetime.fromisoformat(self.completed_at)
            except ValueError as exc:
                raise CRMPrimitiveError(
                    "completed_at must be ISO-8601"
                ) from exc
        if self.related_to_entity_type is not None:
            _require_text("related_to_entity_type", self.related_to_entity_type)
            _require_text("related_to_entity_id", self.related_to_entity_id)


@dataclass(frozen=True)
class PipelineStage:
    resource: CRMResource
    name: str
    probability: int  # percentage 0-100
    order: int

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "PIPELINE_STAGE":
            raise CRMPrimitiveError(
                "resource entity_type must be PIPELINE_STAGE"
            )
        _require_text("name", self.name)
        if not (0 <= self.probability <= 100):
            raise CRMPrimitiveError(
                "probability must be between 0 and 100"
            )
        if not isinstance(self.order, int):
            raise CRMPrimitiveError(
                "order must be an integer"
            )


@dataclass(frozen=True)
class Deal:
    resource: CRMResource
    pipeline_stage_id: str
    amount: Money | None = None
    expected_close_at: str | None = None
    related_to_entity_type: str | None = None  # e.g., CUSTOMER
    related_to_entity_id: str | None = None

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "DEAL":
            raise CRMPrimitiveError(
                "resource entity_type must be DEAL"
            )
        _require_text("pipeline_stage_id", self.pipeline_stage_id)
        if self.amount is not None:
            self.amount.validate()
        if self.expected_close_at is not None:
            try:
                datetime.fromisoformat(self.expected_close_at)
            except ValueError as exc:
                raise CRMPrimitiveError(
                    "expected_close_at must be ISO-8601"
                ) from exc
        if self.related_to_entity_type is not None:
            _require_text("related_to_entity_type", self.related_to_entity_type)
            _require_text("related_to_entity_id", self.related_to_entity_id)


# We can add more entities as needed, but for now we have Activity, PipelineStage, Deal.