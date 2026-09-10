from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from kernel.analytics.runtime import (
    AnalyticsPrimitiveError,
    Money,
    TenantScope,
    AnalyticsResource,
    Metric,
    Dashboard,
    Report,
    Export,
    WarehouseEvent,
)


class AnalyticsServiceError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise AnalyticsServiceError(f"{name} must not be empty")
    result = str(value).strip()
    if not result:
        raise AnalyticsServiceError(f"{name} must not be empty")
    return result


def _time(value: str | None = None) -> str:
    from datetime import datetime, timezone
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise AnalyticsServiceError("requested_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise AnalyticsServiceError("requested_at must be timezone-aware")
    return parsed.isoformat()


def _validate_context(context: Any) -> None:
    if hasattr(context, "validate"):
        context.validate()


@dataclass(frozen=True)
class MetricCreateRequest:
    metric_id: str
    name: str
    formula: str
    description: str | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("metric_id", self.metric_id)
        _text("idempotency_key", self.idempotency_key)
        _text("name", self.name)
        _text("formula", self.formula)
        if self.description is not None and len(self.description) > 2000:
            raise AnalyticsServiceError("description must not exceed 2000 characters")
        return {
            "metric_id": self.metric_id,
            "name": self.name,
            "formula": self.formula,
            "description": self.description,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class DashboardCreateRequest:
    dashboard_id: str
    name: str
    description: str | None = None
    widgets: List[Dict[str, Any]] = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("dashboard_id", self.dashboard_id)
        _text("idempotency_key", self.idempotency_key)
        _text("name", self.name)
        if self.description is not None and len(self.description) > 2000:
            raise AnalyticsServiceError("description must not exceed 2000 characters")
        if self.widgets is None:
            widgets = []
        else:
            if not isinstance(self.widgets, list):
                raise AnalyticsServiceError("widgets must be a list")
            widgets = self.widgets
        return {
            "dashboard_id": self.dashboard_id,
            "name": self.name,
            "description": self.description,
            "widgets": widgets,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class ReportCreateRequest:
    report_id: str
    name: str
    description: str | None = None
    metric_ids: List[str] = None
    filters: Dict[str, Any] = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("report_id", self.report_id)
        _text("idempotency_key", self.idempotency_key)
        _text("name", self.name)
        if self.description is not None and len(self.description) > 2000:
            raise AnalyticsServiceError("description must not exceed 2000 characters")
        if self.metric_ids is None:
            metric_ids = []
        else:
            if not isinstance(self.metric_ids, list):
                raise AnalyticsServiceError("metric_ids must be a list")
            for metric_id in self.metric_ids:
                _text("metric_id", metric_id)
            metric_ids = self.metric_ids
        if self.filters is None:
            filters = {}
        else:
            if not isinstance(self.filters, dict):
                raise AnalyticsServiceError("filters must be a dict")
            filters = self.filters
        return {
            "report_id": self.report_id,
            "name": self.name,
            "description": self.description,
            "metric_ids": metric_ids,
            "filters": filters,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class ExportCreateRequest:
    export_id: str
    name: str
    description: str | None = None
    format: str
    report_id: str
    parameters: Dict[str, Any] = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("export_id", self.export_id)
        _text("idempotency_key", self.idempotency_key)
        _text("name", self.name)
        _text("format", self.format)
        _text("report_id", self.report_id)
        if self.description is not None and len(self.description) > 2000:
            raise AnalyticsServiceError("description must not exceed 2000 characters")
        if self.parameters is None:
            parameters = {}
        else:
            if not isinstance(self.parameters, dict):
                raise AnalyticsServiceError("parameters must be a dict")
            parameters = self.parameters
        return {
            "export_id": self.export_id,
            "name": self.name,
            "description": self.description,
            "format": self.format,
            "report_id": self.report_id,
            "parameters": parameters,
            "requested_at": _time(self.requested_at),
        }


class AnalyticsService:
    def __init__(
        self,
        *,
        foundation: Any,
        product_command_type: Any,
    ) -> None:
        self._foundation = foundation
        self._product_command_type = product_command_type

    def plan_create_metric(
        self,
        *,
        context: Any,
        request: MetricCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="METRIC",
                entity_id=request.metric_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "ANALYTICS_METRIC",
                },
            )
        )

    def plan_create_dashboard(
        self,
        *,
        context: Any,
        request: DashboardCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="DASHBOARD",
                entity_id=request.dashboard_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "ANALYTICS_DASHBOARD",
                },
            )
        )

    def plan_create_report(
        self,
        *,
        context: Any,
        request: ReportCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="REPORT",
                entity_id=request.report_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "ANALYTICS_REPORT",
                },
            )
        )

    def plan_create_export(
        self,
        *,
        context: Any,
        request: ExportCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="EXPORT",
                entity_id=request.export_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "ANALYTICS_EXPORT",
                },
            )
        )

    # We can add update and other methods as needed.