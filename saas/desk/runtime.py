from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kernel.desk.runtime import (
    Ticket,
    Queue,
    KnowledgeArticle,
    SLA,
    DeskPrimitiveError,
    Money,
    TenantScope,
    DeskResource,
)


class DeskSError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise DeskSError(f"{name} must not be empty")
    result = str(value).strip()
    if not result:
        raise DeskSError(f"{name} must not be empty")
    return result


def _time(value: str | None = None) -> str:
    from datetime import datetime, timezone
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise DeskSError("requested_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise DeskSError("requested_at must be timezone-aware")
    return parsed.isoformat()


def _validate_context(context: Any) -> None:
    if hasattr(context, "validate"):
        context.validate()


@dataclass(frozen=True)
class TicketCreateRequest:
    ticket_id: str
    title: str
    description: str | None = None
    status: str
    priority: str
    assignee_id: str | None = None
    requester_id: str | None = None
    queue_id: str | None = None
    sla_id: str | None = None
    tags: list[str] | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("ticket_id", self.ticket_id)
        _text("idempotency_key", self.idempotency_key)
        _text("title", self.title)
        _text("status", self.status)
        _text("priority", self.priority)

        description = self.description or ""
        if len(description) > 5000:
            raise DeskSError("description must not exceed 5000 characters")

        if self.assignee_id is not None:
            _text("assignee_id", self.assignee_id)
        if self.requester_id is not None:
            _text("requester_id", self.requester_id)
        if self.queue_id is not None:
            _text("queue_id", self.queue_id)
        if self.sla_id is not None:
            _text("sla_id", self.sla_id)

        tags = self.tags or []
        if not isinstance(tags, list):
            raise DeskSError("tags must be a list")
        for tag in tags:
            if not isinstance(tag, str):
                raise DeskSError("each tag must be a string")
            if len(tag) > 100:
                raise DeskSError("each tag must not exceed 100 characters")

        return {
            "ticket_id": self.ticket_id,
            "title": self.title,
            "description": description,
            "status": self.status,
            "priority": self.priority,
            "assignee_id": self.assignee_id,
            "requester_id": self.requester_id,
            "queue_id": self.queue_id,
            "sla_id": self.sla_id,
            "tags": tags,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class QueueCreateRequest:
    queue_id: str
    name: str
    description: str | None = None
    routing_type: str
    active: bool | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("queue_id", self.queue_id)
        _text("idempotency_key", self.idempotency_key)
        _text("name", self.name)

        if self.description is not None and len(self.description) > 2000:
            raise DeskSError("description must not exceed 2000 characters")

        _text("routing_type", self.routing_type)

        active = self.active if self.active is not None else True
        if not isinstance(active, bool):
            raise DeskSError("active must be a boolean")

        return {
            "queue_id": self.queue_id,
            "name": self.name,
            "description": self.description,
            "routing_type": self.routing_type,
            "active": active,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class KnowledgeArticleCreateRequest:
    article_id: str
    title: str
    content: str
    category: str | None = None
    is_public: bool | None = None
    version: int | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("article_id", self.article_id)
        _text("idempotency_key", self.idempotency_key)
        _text("title", self.title)
        _text("content", self.content)

        if self.category is not None and len(self.category) > 200:
            raise DeskSError("category must not exceed 200 characters")

        is_public = self.is_public if self.is_public is not None else False
        if not isinstance(is_public, bool):
            raise DeskSError("is_public must be a boolean")

        version = self.version if self.version is not None else 1
        if not isinstance(version, int) or version < 1:
            raise DeskSError("version must be a positive integer")

        return {
            "article_id": self.article_id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "is_public": is_public,
            "version": version,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class SLACreateRequest:
    sla_id: str
    name: str
    description: str | None = None
    response_time_minutes: int
    resolution_time_minutes: int
    business_hours_only: bool | None = None
    active: bool | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("sla_id", self.sla_id)
        _text("idempotency_key", self.idempotency_key)
        _text("name", self.name)

        if self.description is not None and len(self.description) > 2000:
            raise DeskSError("description must not exceed 2000 characters")

        if not isinstance(self.response_time_minutes, int) or self.response_time_minutes < 0:
            raise DeskSError("response_time_minutes must be a non-negative integer")
        if not isinstance(self.resolution_time_minutes, int) or self.resolution_time_minutes < 0:
            raise DeskSError("resolution_time_minutes must be a non-negative integer")

        business_hours_only = self.business_hours_only if self.business_hours_only is not None else False
        if not isinstance(business_hours_only, bool):
            raise DeskSError("business_hours_only must be a boolean")

        active = self.active if self.active is not None else True
        if not isinstance(active, bool):
            raise DeskSError("active must be a boolean")

        return {
            "sla_id": self.sla_id,
            "name": self.name,
            "description": self.description,
            "response_time_minutes": self.response_time_minutes,
            "resolution_time_minutes": self.resolution_time_minutes,
            "business_hours_only": business_hours_only,
            "active": active,
            "requested_at": _time(self.requested_at),
        }


class DeskService:
    def __init__(
        self,
        *,
        foundation: Any,
        product_command_type: Any,
    ) -> None:
        self._foundation = foundation
        self._product_command_type = product_command_type

    def plan_create_ticket(
        self,
        *,
        context: Any,
        request: TicketCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="TICKET",
                entity_id=request.ticket_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "DESK_TICKET",
                },
            )
        )

    def plan_create_queue(
        self,
        *,
        context: Any,
        request: QueueCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="QUEUE",
                entity_id=request.queue_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "DESK_QUEUE",
                },
            )
        )

    def plan_create_knowledge_article(
        self,
        *,
        context: Any,
        request: KnowledgeArticleCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="KNOWLEDGE_ARTICLE",
                entity_id=request.article_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "DESK_KNOWLEDGE_ARTICLE",
                },
            )
        )

    def plan_create_sla(
        self,
        *,
        context: Any,
        request: SLACreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="SLA",
                entity_id=request.sla_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "DESK_SLA",
                },
            )
        )