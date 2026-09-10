from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kernel.automate.runtime import (
    Trigger,
    Workflow,
    Action,
    Run,
    Template,
    AutomatePrimitiveError,
    Money,
    TenantScope,
    AutomateResource,
)


class AutomateSError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise AutomateSError(f"{name} must not be empty")
    result = str(value).strip()
    if not result:
        raise AutomateSError(f"{name} must not be empty")
    return result


def _time(value: str | None = None) -> str:
    from datetime import datetime, timezone
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise AutomateSError("requested_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise AutomateSError("requested_at must be timezone-aware")
    return parsed.isoformat()


def _validate_context(context: Any) -> None:
    if hasattr(context, "validate"):
        context.validate()


@dataclass(frozen=True)
class TriggerCreateRequest:
    trigger_id: str
    name: str
    trigger_type: str
    configuration: dict[str, Any] | None = None
    active: bool | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("trigger_id", self.trigger_id)
        _text("idempotency_key", self.idempotency_key)
        _text("name", self.name)
        _text("trigger_type", self.trigger_type)

        configuration = self.configuration or {}
        if not isinstance(configuration, dict):
            raise AutomateSError("configuration must be a dict")

        active = self.active if self.active is not None else True
        if not isinstance(active, bool):
            raise AutomateSError("active must be a boolean")

        return {
            "trigger_id": self.trigger_id,
            "name": self.name,
            "trigger_type": self.trigger_type,
            "configuration": configuration,
            "active": active,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class WorkflowCreateRequest:
    workflow_id: str
    name: str
    description: str | None = None
    definition: dict[str, Any]
    active: bool | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("workflow_id", self.workflow_id)
        _text("idempotency_key", self.idempotency_key)
        _text("name", self.name)

        if self.description is not None and len(self.description) > 2000:
            raise AutomateSError("description must not exceed 2000 characters")

        if not isinstance(self.definition, dict):
            raise AutomateSError("definition must be a dict")

        active = self.active if self.active is not None else True
        if not isinstance(active, bool):
            raise AutomateSError("active must be a boolean")

        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "definition": self.definition,
            "active": active,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class ActionCreateRequest:
    action_id: str
    name: str
    action_type: str
    configuration: dict[str, Any] | None = None
    active: bool | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("action_id", self.action_id)
        _text("idempotency_key", self.idempotency_key)
        _text("name", self.name)
        _text("action_type", self.action_type)

        configuration = self.configuration or {}
        if not isinstance(configuration, dict):
            raise AutomateSError("configuration must be a dict")

        active = self.active if self.active is not None else True
        if not isinstance(active, bool):
            raise AutomateSError("active must be a boolean")

        return {
            "action_id": self.action_id,
            "name": self.name,
            "action_type": self.action_type,
            "configuration": configuration,
            "active": active,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class RunCreateRequest:
    run_id: str
    workflow_id: str
    trigger_id: str | None = None
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    inputs: dict[str, Any] | None = None
    outputs: dict[str, Any] | None = None
    error: str | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("run_id", self.run_id)
        _text("idempotency_key", self.idempotency_key)
        _text("workflow_id", self.workflow_id)
        if self.trigger_id is not None:
            _text("trigger_id", self.trigger_id)
        _text("status", self.status)

        if self.started_at is not None:
            try:
                from datetime import datetime
                datetime.fromisoformat(self.started_at)
            except ValueError:
                raise AutomateSError("started_at must be ISO-8601")
        if self.completed_at is not None:
            try:
                from datetime import datetime
                datetime.fromisoformat(self.completed_at)
            except ValueError:
                raise AutomateSError("completed_at must be ISO-8601")

        inputs = self.inputs or {}
        if not isinstance(inputs, dict):
            raise AutomateSError("inputs must be a dict")
        outputs = self.outputs or {}
        if not isinstance(outputs, dict):
            raise AutomateSError("outputs must be a dict")
        if self.error is not None and len(self.error) > 2000:
            raise AutomateSError("error must not exceed 2000 characters")

        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "trigger_id": self.trigger_id,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "inputs": inputs,
            "outputs": outputs,
            "error": self.error,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class TemplateCreateRequest:
    template_id: str
    name: str
    description: str | None = None
    workflow_definition: dict[str, Any]
    active: bool | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("template_id", self.template_id)
        _text("idempotency_key", self.idempotency_key)
        _text("name", self.name)

        if self.description is not None and len(self.description) > 2000:
            raise AutomateSError("description must not exceed 2000 characters")

        if not isinstance(self.workflow_definition, dict):
            raise AutomateSError("workflow_definition must be a dict")

        active = self.active if self.active is not None else True
        if not isinstance(active, bool):
            raise AutomateSError("active must be a boolean")

        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "workflow_definition": self.workflow_definition,
            "active": active,
            "requested_at": _time(self.requested_at),
        }


class AutomateService:
    def __init__(
        self,
        *,
        foundation: Any,
        product_command_type: Any,
    ) -> None:
        self._foundation = foundation
        self._product_command_type = product_command_type

    def plan_create_trigger(
        self,
        *,
        context: Any,
        request: TriggerCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="TRIGGER",
                entity_id=request.trigger_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "AUTOMATE_TRIGGER",
                },
            )
        )

    def plan_create_workflow(
        self,
        *,
        context: Any,
        request: WorkflowCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="WORKFLOW",
                entity_id=request.workflow_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "AUTOMATE_WORKFLOW",
                },
            )
        )

    def plan_create_action(
        self,
        *,
        context: Any,
        request: ActionCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="ACTION",
                entity_id=request.action_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "AUTOMATE_ACTION",
                },
            )
        )

    def plan_create_run(
        self,
        *,
        context: Any,
        request: RunCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="RUN",
                entity_id=request.run_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "AUTOMATE_RUN",
                },
            )
        )

    def plan_create_template(
        self,
        *,
        context: Any,
        request: TemplateCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="TEMPLATE",
                entity_id=request.template_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "AUTOMATE_TEMPLATE",
                },
            )
        )