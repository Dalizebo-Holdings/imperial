from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Any, Dict, List, Optional


class ProjectsPrimitiveError(ValueError):
    pass


def _require_text(name: str, value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ProjectsPrimitiveError(
            f"{name} must not be empty"
        )
    return normalized


def validate_currency(currency: str) -> str:
    value = str(currency).strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", value):
        raise ProjectsPrimitiveError(
            "currency must be three uppercase letters"
        )
    return value


@dataclass(frozen=True)
class Money:
    amount_minor: int
    currency: str

    def validate(self, *, allow_negative: bool = False) -> None:
        if not isinstance(self.amount_minor, int):
            raise ProjectsPrimitiveError(
                "amount_minor must be an integer"
            )
        if not allow_negative and self.amount_minor < 0:
            raise ProjectsPrimitiveError(
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
class ProjectsResource:
    id: str
    entity_type: str
    tenant: TenantScope
    created_at: str
    updated_at: str

    def validate(self) -> None:
        _require_text("id", self.id)

        if self.entity_type not in PROJECTS_ENTITY_TYPES:
            raise ProjectsPrimitiveError(
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
                raise ProjectsPrimitiveError(
                    f"{name} must be ISO-8601"
                ) from exc


# Entity types for Projects
PROJECTS_ENTITY_TYPES = {
    "PROJECT",
    "TASK",
    "TEAM",
    "TIMELINE",
}


@dataclass(frozen=True)
class Project:
    resource: ProjectsResource
    name: str
    description: str | None = None
    status: str  # e.g., "PLANNING", "ACTIVE", "ON_HOLD", "COMPLETED", "CANCELLED"
    start_date: str | None = None
    end_date: str | None = None
    budget: Money | None = None
    owner_id: str | None = None
    tags: List[str] = field(default_factory=list)

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "PROJECT":
            raise ProjectsPrimitiveError(
                "resource entity_type must be PROJECT"
            )
        _require_text("name", self.name)
        if self.description is not None and len(self.description) > 5000:
            raise ProjectsPrimitiveError(
                "description must not exceed 5000 characters"
            )
        _require_text("status", self.status)
        if self.start_date is not None:
            try:
                datetime.fromisoformat(self.start_date)
            except ValueError as exc:
                raise ProjectsPrimitiveError(
                    "start_date must be ISO-8601"
                ) from exc
        if self.end_date is not None:
            try:
                datetime.fromisoformat(self.end_date)
            except ValueError as exc:
                raise ProjectsPrimitiveError(
                    "end_date must be ISO-8601"
                ) from exc
        if self.budget is not None:
            self.budget.validate()
        if self.owner_id is not None:
            _require_text("owner_id", self.owner_id)
        if not isinstance(self.tags, list):
            raise ProjectsPrimitiveError(
                "tags must be a list"
            )
        for tag in self.tags:
            if not isinstance(tag, str):
                raise ProjectsPrimitiveError(
                    "each tag must be a string"
                )
            if len(tag) > 100:
                raise ProjectsPrimitiveError(
                    "each tag must not exceed 100 characters"
                )


@dataclass(frozen=True)
class Task:
    resource: ProjectsResource
    project_id: str
    name: str
    description: str | None = None
    status: str  # e.g., "TODO", "IN_PROGRESS", "REVIEW", "DONE"
    priority: str  # e.g., "LOW", "MEDIUM", "HIGH", "URGENT"
    assignee_id: str | None = None
    estimated_hours: float | None = None
    actual_hours: float | None = None
    start_date: str | None = None
    due_date: str | None = None
    dependencies: List[str] = field(default_factory=list)

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "TASK":
            raise ProjectsPrimitiveError(
                "resource entity_type must be TASK"
            )
        _require_text("project_id", self.project_id)
        _require_text("name", self.name)
        if self.description is not None and len(self.description) > 5000:
            raise ProjectsPrimitiveError(
                "description must not exceed 5000 characters"
            )
        _require_text("status", self.status)
        _require_text("priority", self.priority)
        if self.assignee_id is not None:
            _require_text("assignee_id", self.assignee_id)
        if self.estimated_hours is not None:
            if not isinstance(self.estimated_hours, (int, float)) or self.estimated_hours < 0:
                raise ProjectsPrimitiveError(
                    "estimated_hours must be a non-negative number"
                )
        if self.actual_hours is not None:
            if not isinstance(self.actual_hours, (int, float)) or self.actual_hours < 0:
                raise ProjectsPrimitiveError(
                    "actual_hours must be a non-negative number"
                )
        if self.start_date is not None:
            try:
                datetime.fromisoformat(self.start_date)
            except ValueError as exc:
                raise ProjectsPrimitiveError(
                    "start_date must be ISO-8601"
                ) from exc
        if self.due_date is not None:
            try:
                datetime.fromisoformat(self.due_date)
            except ValueError as exc:
                raise ProjectsPrimitiveError(
                    "due_date must be ISO-8601"
                ) from exc
        if not isinstance(self.dependencies, list):
            raise ProjectsPrimitiveError(
                "dependencies must be a list"
            )
        for dep in self.dependencies:
            if not isinstance(dep, str):
                raise ProjectsPrimitiveError(
                    "each dependency must be a string"
                )


@dataclass(frozen=True)
class Team:
    resource: ProjectsResource
    name: str
    description: str | None = None
    project_id: str | None = None
    members: List[str] = field(default_factory=list)
    roles: Dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "TEAM":
            raise ProjectsPrimitiveError(
                "resource entity_type must be TEAM"
            )
        _require_text("name", self.name)
        if self.description is not None and len(self.description) > 2000:
            raise ProjectsPrimitiveError(
                "description must not exceed 2000 characters"
            )
        if self.project_id is not None:
            _require_text("project_id", self.project_id)
        if not isinstance(self.members, list):
            raise ProjectsPrimitiveError(
                "members must be a list"
            )
        for member in self.members:
            if not isinstance(member, str):
                raise ProjectsPrimitiveError(
                    "each member must be a string"
                )
            _require_text("member", member)
        if not isinstance(self.roles, dict):
            raise ProjectsPrimitiveError(
                "roles must be a dict"
            )
        for role_name, role_value in self.roles.items():
            if not isinstance(role_name, str) or not isinstance(role_value, str):
                raise ProjectsPrimitiveError(
                    "roles must map strings to strings"
                )
            _require_text("role_name", role_name)
            _require_text("role_value", role_value)


@dataclass(frozen=True)
class Timeline:
    resource: ProjectsResource
    project_id: str
    name: str
    description: str | None = None
    start_date: str
    end_date: str
    milestones: List[Dict[str, Any]] = field(default_factory=list)

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "TIMELINE":
            raise ProjectsPrimitiveError(
                "resource entity_type must be TIMELINE"
            )
        _require_text("project_id", self.project_id)
        _require_text("name", self.name)
        if self.description is not None and len(self.description) > 2000:
            raise ProjectsPrimitiveError(
                "description must not exceed 2000 characters"
            )
        _require_text("start_date", self.start_date)
        try:
            datetime.fromisoformat(self.start_date)
        except ValueError as exc:
            raise ProjectsPrimitiveError(
                "start_date must be ISO-8601"
            ) from exc
        _require_text("end_date", self.end_date)
        try:
            datetime.fromisoformat(self.end_date)
        except ValueError as exc:
            raise ProjectsPrimitiveError(
                "end_date must be ISO-8601"
            ) from exc
        if not isinstance(self.milestones, list):
            raise ProjectsPrimitiveError(
                "milestones must be a list"
            )
        for i, milestone in enumerate(self.milestones):
            if not isinstance(milestone, dict):
                raise ProjectsPrimitiveError(
                    f"milestone at index {i} must be a dict"
                )
            if "name" not in milestone or not isinstance(milestone["name"], str):
                raise ProjectsPrimitiveError(
                    f"milestone at index {i} must have a 'name' string field"
                )
            _require_text(f"milestone[{i}].name", milestone["name"])
            if "date" in milestone and milestone["date"] is not None:
                if not isinstance(milestone["date"], str):
                    raise ProjectsPrimitiveError(
                        f"milestone at index {i} date must be a string if present"
                    )
                try:
                    datetime.fromisoformat(milestone["date"])
                except ValueError as exc:
                    raise ProjectsPrimitiveError(
                        f"milestone at index {i} date must be ISO-8601"
                    ) from exc