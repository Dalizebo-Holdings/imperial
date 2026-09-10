from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Any, Dict, List, Optional


class AutomatePrimitiveError(ValueError):
    pass


def _require_text(name: str, value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise AutomatePrimitiveError(
            f"{name} must not be empty"
        )
    return normalized


def validate_currency(currency: str) -> str:
    value = str(currency).strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", value):
        raise AutomatePrimitiveError(
            "currency must be three uppercase letters"
        )
    return value


@dataclass(frozen=True)
class Money:
    amount_minor: int
    currency: str

    def validate(self, *, allow_negative: bool = False) -> None:
        if not isinstance(self.amount_minor, int):
            raise AutomatePrimitiveError(
                "amount_minor must be an integer"
            )
        if not allow_negative and self.amount_minor < 0:
            raise AutomatePrimitiveError(
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
class AutomateResource:
    id: str
    entity_type: str
    tenant: TenantScope
    created_at: str
    updated_at: str

    def validate(self) -> None:
        _require_text("id", self.id)

        if self.entity_type not in AUTOMATE_ENTITY_TYPES:
            raise AutomatePrimitiveError(
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
                raise AutomatePrimitiveError(
                    f"{name} must be ISO-8601"
                ) from exc


# Entity types for Automate
AUTOMATE_ENTITY_TYPES = {
    "TRIGGER",
    "WORKFLOW",
    "ACTION",
    "RUN",
    "TEMPLATE",
}


@dataclass(frozen=True)
class Trigger:
    resource: AutomateResource
    name: str
    trigger_type: str  # e.g., "EVENT", "SCHEDULE", "WEBHOOK"
    configuration: Dict[str, Any] = field(default_factory=dict)
    active: bool = True

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "TRIGGER":
            raise AutomatePrimitiveError(
                "resource entity_type must be TRIGGER"
            )
        _require_text("name", self.name)
        _require_text("trigger_type", self.trigger_type)
        if not isinstance(self.configuration, dict):
            raise AutomatePrimitiveError(
                "configuration must be a dict"
            )
        if not isinstance(self.active, bool):
            raise AutomatePrimitiveError(
                "active must be a boolean"
            )


@dataclass(frozen=True)
class Workflow:
    resource: AutomateResource
    name: str
    description: str | None = None
    definition: Dict[str, Any]  # DAG structure
    active: bool = True

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "WORKFLOW":
            raise AutomatePrimitiveError(
                "resource entity_type must be WORKFLOW"
            )
        _require_text("name", self.name)
        if self.description is not None and len(self.description) > 2000:
            raise AutomatePrimitiveError(
                "description must not exceed 2000 characters"
            )
        if not isinstance(self.definition, dict):
            raise AutomatePrimitiveError(
                "definition must be a dict"
            )
        if not isinstance(self.active, bool):
            raise AutomatePrimitiveError(
                "active must be a boolean"
            )


@dataclass(frozen=True)
class Action:
    resource: AutomateResource
    name: str
    action_type: str  # e.g., "API", "FUNCTION", "NOTIFICATION"
    configuration: Dict[str, Any] = field(default_factory=dict)
    active: bool = True

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "ACTION":
            raise AutomatePrimitiveError(
                "resource entity_type must be ACTION"
            )
        _require_text("name", self.name)
        _require_text("action_type", self.action_type)
        if not isinstance(self.configuration, dict):
            raise AutomatePrimitiveError(
                "configuration must be a dict"
            )
        if not isinstance(self.active, bool):
            raise AutomatePrimitiveError(
                "active must be a boolean"
            )


@dataclass(frozen=True)
class Run:
    resource: AutomateResource
    workflow_id: str
    trigger_id: str | None = None
    status: str  # e.g., "PENDING", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED"
    started_at: str | None = None
    completed_at: str | None = None
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "RUN":
            raise AutomatePrimitiveError(
                "resource entity_type must be RUN"
            )
        _require_text("workflow_id", self.workflow_id)
        if self.trigger_id is not None:
            _require_text("trigger_id", self.trigger_id)
        _require_text("status", self.status)
        if self.started_at is not None:
            try:
                datetime.fromisoformat(self.started_at)
            except ValueError as exc:
                raise AutomatePrimitiveError(
                    "started_at must be ISO-8601"
                ) from exc
        if self.completed_at is not None:
            try:
                datetime.fromisoformat(self.completed_at)
            except ValueError as exc:
                raise AutomatePrimitiveError(
                    "completed_at must be ISO-8601"
                ) from exc
        if not isinstance(self.inputs, dict):
            raise AutomatePrimitiveError(
                "inputs must be a dict"
            )
        if not isinstance(self.outputs, dict):
            raise AutomatePrimitiveError(
                "outputs must be a dict"
            )
        if self.error is not None and len(self.error) > 2000:
            raise AutomatePrimitiveError(
                "error must not exceed 2000 characters"
            )


@dataclass(frozen=True)
class Template:
    resource: AutomateResource
    name: str
    description: str | None = None
    workflow_definition: Dict[str, Any]
    active: bool = True

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "TEMPLATE":
            raise AutomatePrimitiveError(
                "resource entity_type must be TEMPLATE"
            )
        _require_text("name", self.name)
        if self.description is not None and len(self.description) > 2000:
            raise AutomatePrimitiveError(
                "description must not exceed 2000 characters"
            )
        if not isinstance(self.workflow_definition, dict):
            raise AutomatePrimitiveError(
                "workflow_definition must be a dict"
            )
        if not isinstance(self.active, bool):
            raise AutomatePrimitiveError(
                "active must be a boolean"
            )