from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kernel.projects.runtime import (
    Project,
    Task,
    Team,
    Timeline,
    ProjectsPrimitiveError,
    Money,
    TenantScope,
    ProjectsResource,
)


class ProjectsSError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise ProjectsSError(f"{name} must not be empty")
    result = str(value).strip()
    if not result:
        raise ProjectsSError(f"{name} must not be empty")
    return result


def _time(value: str | None = None) -> str:
    from datetime import datetime, timezone
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ProjectsSError("requested_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ProjectsSError("requested_at must be timezone-aware")
    return parsed.isoformat()


def _validate_context(context: Any) -> None:
    if hasattr(context, "validate"):
        context.validate()


@dataclass(frozen=True)
class ProjectCreateRequest:
    project_id: str
    name: str
    description: str | None = None
    status: str
    start_date: str | None = None
    end_date: str | None = None
    budget: dict[str, Any] | None = None  # Expecting {amount_minor: int, currency: str}
    owner_id: str | None = None
    tags: list[str] | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("project_id", self.project_id)
        _text("idempotency_key", self.idempotency_key)
        _text("name", self.name)
        _text("status", self.status)

        description = self.description or ""
        if len(description) > 5000:
            raise ProjectsSError("description must not exceed 5000 characters")

        if self.start_date is not None:
            try:
                from datetime import datetime
                datetime.fromisoformat(self.start_date)
            except ValueError:
                raise ProjectsSError("start_date must be ISO-8601")
        if self.end_date is not None:
            try:
                from datetime import datetime
                datetime.fromisoformat(self.end_date)
            except ValueError:
                raise ProjectsSError("end_date must be ISO-8601")

        budget = None
        if self.budget is not None:
            if not isinstance(self.budget, dict):
                raise ProjectsSError("budget must be a dict with amount_minor and currency")
            amount_minor = self.budget.get("amount_minor")
            currency = self.budget.get("currency")
            if not isinstance(amount_minor, int):
                raise ProjectsSError("amount_minor must be an integer")
            if not isinstance(currency, str):
                raise ProjectsSError("currency must be a string")
            # Validate currency format (three uppercase letters)
            import re
            if not re.fullmatch(r"[A-Z]{3}", currency):
                raise ProjectsSError("currency must be three uppercase letters")
            budget = {"amount_minor": amount_minor, "currency": currency}

        if self.owner_id is not None:
            _text("owner_id", self.owner_id)

        tags = self.tags or []
        if not isinstance(tags, list):
            raise ProjectsSError("tags must be a list")
        for tag in tags:
            if not isinstance(tag, str):
                raise ProjectsSError("each tag must be a string")
            if len(tag) > 100:
                raise ProjectsSError("each tag must not exceed 100 characters")

        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": description,
            "status": self.status,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "budget": budget,
            "owner_id": self.owner_id,
            "tags": tags,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class TaskCreateRequest:
    task_id: str
    project_id: str
    name: str
    description: str | None = None
    status: str
    priority: str
    assignee_id: str | None = None
    estimated_hours: float | None = None
    actual_hours: float | None = None
    start_date: str | None = None
    due_date: str | None = None
    dependencies: list[str] | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("task_id", self.task_id)
        _text("idempotency_key", self.idempotency_key)
        _text("project_id", self.project_id)
        _text("name", self.name)
        _text("status", self.status)
        _text("priority", self.priority)

        description = self.description or ""
        if len(description) > 5000:
            raise ProjectsSError("description must not exceed 5000 characters")

        if self.assignee_id is not None:
            _text("assignee_id", self.assignee_id)
        if self.estimated_hours is not None:
            if not isinstance(self.estimated_hours, (int, float)) or self.estimated_hours < 0:
                raise ProjectsSError("estimated_hours must be a non-negative number")
        if self.actual_hours is not None:
            if not isinstance(self.actual_hours, (int, float)) or self.actual_hours < 0:
                raise ProjectsSError("actual_hours must be a non-negative number")
        if self.start_date is not None:
            try:
                from datetime import datetime
                datetime.fromisoformat(self.start_date)
            except ValueError:
                raise ProjectsSError("start_date must be ISO-8601")
        if self.due_date is not None:
            try:
                from datetime import datetime
                datetime.fromisoformat(self.due_date)
            except ValueError:
                raise ProjectsSError("due_date must be ISO-8601")

        dependencies = self.dependencies or []
        if not isinstance(dependencies, list):
            raise ProjectsSError("dependencies must be a list")
        for dep in dependencies:
            if not isinstance(dep, str):
                raise ProjectsSError("each dependency must be a string")

        return {
            "task_id": self.task_id,
            "project_id": self.project_id,
            "name": self.name,
            "description": description,
            "status": self.status,
            "priority": self.priority,
            "assignee_id": self.assignee_id,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "start_date": self.start_date,
            "due_date": self.due_date,
            "dependencies": dependencies,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class TeamCreateRequest:
    team_id: str
    name: str
    description: str | None = None
    project_id: str | None = None
    members: list[str] | None = None
    roles: dict[str, str] | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("team_id", self.team_id)
        _text("idempotency_key", self.idempotency_key)
        _text("name", self.name)

        if self.description is not None and len(self.description) > 2000:
            raise ProjectsSError("description must not exceed 2000 characters")

        if self.project_id is not None:
            _text("project_id", self.project_id)

        members = self.members or []
        if not isinstance(members, list):
            raise ProjectsSError("members must be a list")
        for member in members:
            if not isinstance(member, str):
                raise ProjectsSError("each member must be a string")
            _text("member", member)

        roles = self.roles or {}
        if not isinstance(roles, dict):
            raise ProjectsSError("roles must be a dict")
        for role_name, role_value in roles.items():
            if not isinstance(role_name, str) or not isinstance(role_value, str):
                raise ProjectsSError("roles must map strings to strings")
            _text("role_name", role_name)
            _text("role_value", role_value)

        return {
            "team_id": self.team_id,
            "name": self.name,
            "description": self.description,
            "project_id": self.project_id,
            "members": members,
            "roles": roles,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class TimelineCreateRequest:
    timeline_id: str
    project_id: str
    name: str
    description: str | None = None
    start_date: str
    end_date: str
    milestones: list[dict[str, Any]] | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("timeline_id", self.timeline_id)
        _text("idempotency_key", self.idempotency_key)
        _text("project_id", self.project_id)
        _text("name", self.name)

        if self.description is not None and len(self.description) > 2000:
            raise ProjectsSError("description must not exceed 2000 characters")

        _text("start_date", self.start_date)
        try:
            from datetime import datetime
            datetime.fromisoformat(self.start_date)
        except ValueError:
            raise ProjectsSError("start_date must be ISO-8601")
        _text("end_date", self.end_date)
        try:
            from datetime import datetime
            datetime.fromisoformat(self.end_date)
        except ValueError:
            raise ProjectsSError("end_date must be ISO-8601")

        milestones = self.milestones or []
        if not isinstance(milestones, list):
            raise ProjectsSError("milestones must be a list")
        for i, milestone in enumerate(milestones):
            if not isinstance(milestone, dict):
                raise ProjectsSError(f"milestone at index {i} must be a dict")
            if "name" not in milestone or not isinstance(milestone["name"], str):
                raise ProjectsSError(f"milestone at index {i} must have a 'name' string field")
            _text(f"milestone[{i}].name", milestone["name"])
            if "date" in milestone and milestone["date"] is not None:
                if not isinstance(milestone["date"], str):
                    raise ProjectsSError(f"milestone at index {i} date must be a string if present")
                try:
                    from datetime import datetime
                    datetime.fromisoformat(milestone["date"])
                except ValueError:
                    raise ProjectsSError(f"milestone at index {i} date must be ISO-8601")

        return {
            "timeline_id": self.timeline_id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "milestones": milestones,
            "requested_at": _time(self.requested_at),
        }


class ProjectsService:
    def __init__(
        self,
        *,
        foundation: Any,
        product_command_type: Any,
    ) -> None:
        self._foundation = foundation
        self._product_command_type = product_command_type

    def plan_create_project(
        self,
        *,
        context: Any,
        request: ProjectCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="PROJECT",
                entity_id=request.project_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "PROJECTS_PROJECT",
                },
            )
        )

    def plan_create_task(
        self,
        *,
        context: Any,
        request: TaskCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="TASK",
                entity_id=request.task_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "PROJECTS_TASK",
                },
            )
        )

    def plan_create_team(
        self,
        *,
        context: Any,
        request: TeamCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="TEAM",
                entity_id=request.team_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "PROJECTS_TEAM",
                },
            )
        )

    def plan_create_timeline(
        self,
        *,
        context: Any,
        request: TimelineCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="TIMELINE",
                entity_id=request.timeline_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "PROJECTS_TIMELINE",
                },
            )
        )