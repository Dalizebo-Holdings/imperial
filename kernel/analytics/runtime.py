from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Any, Dict, List, Optional


class AnalyticsPrimitiveError(ValueError):
    pass


def _require_text(name: str, value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise AnalyticsPrimitiveError(
            f"{name} must not be empty"
        )
    return normalized


def validate_currency(currency: str) -> str:
    value = str(currency).strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", value):
        raise AnalyticsPrimitiveError(
            "currency must be three uppercase letters"
        )
    return value


@dataclass(frozen=True)
class Money:
    amount_minor: int
    currency: str

    def validate(self, *, allow_negative: bool = False) -> None:
        if not isinstance(self.amount_minor, int):
            raise AnalyticsPrimitiveError(
                "amount_minor must be an integer"
            )
        if not allow_negative and self.amount_minor < 0:
            raise AnalyticsPrimitiveError(
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
class AnalyticsResource:
    id: str
    entity_type: str
    tenant: TenantScope
    created_at: str
    updated_at: str

    def validate(self) -> None:
        _require_text("id", self.id)

        if self.entity_type not in ANALYTICS_ENTITY_TYPES:
            raise AnalyticsPrimitiveError(
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
                raise AnalyticsPrimitiveError(
                    f"{name} must be ISO-8601"
                ) from exc


# Entity types for Analytics
ANALYTICS_ENTITY_TYPES = {
    "METRIC",
    "DASHBOARD",
    "REPORT",
    "EXPORT",
    "WAREHOUSE_EVENT",
}


@dataclass(frozen=True)
class Metric:
    resource: AnalyticsResource
    name: str
    formula: str  # e.g., "SUM(amount_minor)" or "COUNT(*)"
    description: str | None = None

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "METRIC":
            raise AnalyticsPrimitiveError(
                "resource entity_type must be METRIC"
            )
        _require_text("name", self.name)
        _require_text("formula", self.formula)
        if self.description is not None and len(self.description) > 2000:
            raise AnalyticsPrimitiveError(
                "description must not exceed 2000 characters"
            )


@dataclass(frozen=True)
class Dashboard:
    resource: AnalyticsResource
    name: str
    description: str | None = None
    widgets: List[Dict[str, Any]] = field(default_factory=list)

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "DASHBOARD":
            raise AnalyticsPrimitiveError(
                "resource entity_type must be DASHBOARD"
            )
        _require_text("name", self.name)
        if self.description is not None and len(self.description) > 2000:
            raise AnalyticsPrimitiveError(
                "description must not exceed 2000 characters"
            )
        # Validate widgets structure? For now, just ensure it's a list.
        if not isinstance(self.widgets, list):
            raise AnalyticsPrimitiveError(
                "widgets must be a list"
            )


@dataclass(frozen=True)
class Report:
    resource: AnalyticsResource
    name: str
    description: str | None = None
    metric_ids: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "REPORT":
            raise AnalyticsPrimitiveError(
                "resource entity_type must be REPORT"
            )
        _require_text("name", self.name)
        if self.description is not None and len(self.description) > 2000:
            raise AnalyticsPrimitiveError(
                "description must not exceed 2000 characters"
            )
        if not isinstance(self.metric_ids, list):
            raise AnalyticsPrimitiveError(
                "metric_ids must be a list"
            )
        for metric_id in self.metric_ids:
            _require_text("metric_id", metric_id)
        if not isinstance(self.filters, dict):
            raise AnalyticsPrimitiveError(
                "filters must be a dict"
            )


@dataclass(frozen=True)
class Export:
    resource: AnalyticsResource
    name: str
    description: str | None = None
    format: str  # e.g., "CSV", "JSON", "PDF"
    report_id: str
    parameters: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "EXPORT":
            raise AnalyticsPrimitiveError(
                "resource entity_type must be EXPORT"
            )
        _require_text("name", self.name)
        _require_text("format", self.format)
        _require_text("report_id", self.report_id)
        if self.description is not None and len(self.description) > 2000:
            raise AnalyticsPrimitiveError(
                "description must not exceed 2000 characters"
            )
        if not isinstance(self.parameters, dict):
            raise AnalyticsPrimitiveError(
                "parameters must be a dict"
            )


@dataclass(frozen=True)
class WarehouseEvent:
    resource: AnalyticsResource
    event_id: str  # original event ID from source module
    source_module: str  # e.g., "commerce", "pos", "crm"
    event_type: str  # e.g., "order.created", "payment.completed"
    payload: str  # JSON string of the original event payload
    processed_at: str  # timestamp when processed into warehouse

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "WAREHOUSE_EVENT":
            raise AnalyticsPrimitiveError(
                "resource entity_type must be WAREHOUSE_EVENT"
            )
        _require_text("event_id", self.event_id)
        _require_text("source_module", self.source_module)
        _require_text("event_type", self.event_type)
        _require_text("payload", self.payload)
        _require_text("processed_at", self.processed_at)
        # Validate that processed_at is a valid ISO timestamp
        try:
            datetime.fromisoformat(self.processed_at)
        except ValueError as exc:
            raise AnalyticsPrimitiveError(
                "processed_at must be ISO-8601"
            ) from exc