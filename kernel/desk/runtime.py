from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Any, Dict, List, Optional


class DeskPrimitiveError(ValueError):
    pass


def _require_text(name: str, value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise DeskPrimitiveError(
            f"{name} must not be empty"
        )
    return normalized


def validate_currency(currency: str) -> str:
    value = str(currency).strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", value):
        raise DeskPrimitiveError(
            "currency must be three uppercase letters"
        )
    return value


@dataclass(frozen=True)
class Money:
    amount_minor: int
    currency: str

    def validate(self, *, allow_negative: bool = False) -> None:
        if not isinstance(self.amount_minor, int):
            raise DeskPrimitiveError(
                "amount_minor must be an integer"
            )
        if not allow_negative and self.amount_minor < 0:
            raise DeskPrimitiveError(
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
class DeskResource:
    id: str
    entity_type: str
    tenant: TenantScope
    created_at: str
    updated_at: str

    def validate(self) -> None:
        _require_text("id", self.id)

        if self.entity_type not in DESK_ENTITY_TYPES:
            raise DeskPrimitiveError(
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
                raise DeskPrimitiveError(
                    f"{name} must be ISO-8601"
                ) from exc


# Entity types for Desk
DESK_ENTITY_TYPES = {
    "TICKET",
    "QUEUE",
    "KNOWLEDGE_ARTICLE",
    "SLA",
}


@dataclass(frozen=True)
class Ticket:
    resource: DeskResource
    title: str
    description: str | None = None
    status: str  # e.g., "OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"
    priority: str  # e.g., "LOW", "MEDIUM", "HIGH", "URGENT"
    assignee_id: str | None = None
    requester_id: str | None = None
    queue_id: str | None = None
    sla_id: str | None = None
    tags: List[str] = field(default_factory=list)

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "TICKET":
            raise DeskPrimitiveError(
                "resource entity_type must be TICKET"
            )
        _require_text("title", self.title)
        if self.description is not None and len(self.description) > 5000:
            raise DeskPrimitiveError(
                "description must not exceed 5000 characters"
            )
        _require_text("status", self.status)
        _require_text("priority", self.priority)
        if self.assignee_id is not None:
            _require_text("assignee_id", self.assignee_id)
        if self.requester_id is not None:
            _require_text("requester_id", self.requester_id)
        if self.queue_id is not None:
            _require_text("queue_id", self.queue_id)
        if self.sla_id is not None:
            _require_text("sla_id", self.sla_id)
        if not isinstance(self.tags, list):
            raise DeskPrimitiveError(
                "tags must be a list"
            )
        for tag in self.tags:
            if not isinstance(tag, str):
                raise DeskPrimitiveError(
                    "each tag must be a string"
                )
            if len(tag) > 100:
                raise DeskPrimitiveError(
                    "each tag must not exceed 100 characters"
                )


@dataclass(frozen=True)
class Queue:
    resource: DeskResource
    name: str
    description: str | None = None
    routing_type: str  # e.g., "ROUND_ROBIN", "LEAST_BUSY", "SKILL_BASED"
    active: bool = True

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "QUEUE":
            raise DeskPrimitiveError(
                "resource entity_type must be QUEUE"
            )
        _require_text("name", self.name)
        if self.description is not None and len(self.description) > 2000:
            raise DeskPrimitiveError(
                "description must not exceed 2000 characters"
            )
        _require_text("routing_type", self.routing_type)
        if not isinstance(self.active, bool):
            raise DeskPrimitiveError(
                "active must be a boolean"
            )


@dataclass(frozen=True)
class KnowledgeArticle:
    resource: DeskResource
    title: str
    content: str
    category: str | None = None
    is_public: bool = False
    version: int = 1

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "KNOWLEDGE_ARTICLE":
            raise DeskPrimitiveError(
                "resource entity_type must be KNOWLEDGE_ARTICLE"
            )
        _require_text("title", self.title)
        _require_text("content", self.content)
        if self.category is not None and len(self.category) > 200:
            raise DeskPrimitiveError(
                "category must not exceed 200 characters"
            )
        if not isinstance(self.is_public, bool):
            raise DeskPrimitiveError(
                "is_public must be a boolean"
            )
        if not isinstance(self.version, int) or self.version < 1:
            raise DeskPrimitiveError(
                "version must be a positive integer"
            )


@dataclass(frozen=True)
class SLA:
    resource: DeskResource
    name: str
    description: str | None = None
    response_time_minutes: int
    resolution_time_minutes: int
    business_hours_only: bool = False
    active: bool = True

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "SLA":
            raise DeskPrimitiveError(
                "resource entity_type must be SLA"
            )
        _require_text("name", self.name)
        if self.description is not None and len(self.description) > 2000:
            raise DeskPrimitiveError(
                "description must not exceed 2000 characters"
            )
        if not isinstance(self.response_time_minutes, int) or self.response_time_minutes < 0:
            raise DeskPrimitiveError(
                "response_time_minutes must be a non-negative integer"
            )
        if not isinstance(self.resolution_time_minutes, int) or self.resolution_time_minutes < 0:
            raise DeskPrimitiveError(
                "resolution_time_minutes must be a non-negative integer"
            )
        if not isinstance(self.business_hours_only, bool):
            raise DeskPrimitiveError(
                "business_hours_only must be a boolean"
            )
        if not isinstance(self.active, bool):
            raise DeskPrimitiveError(
                "active must be a boolean"
            )