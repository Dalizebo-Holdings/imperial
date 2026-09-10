from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Union

from kernel.developer_cloud.runtime import (
    Project,
    Environment,
    SDK,
    Documentation,
    DeveloperCloudPrimitiveError,
    DeveloperCloudResource,
    TenantScope,
)


class DeveloperCloudSError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise DeveloperCloudSError(f"{name} must not be empty")
    result = str(value).strip()
    if not result:
        raise DeveloperCloudSError(f"{name} must not be empty")
    return result


def _time(value: str | None = None) -> str:
    from datetime import datetime, timezone
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise DeveloperCloudSError("requested_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise DeveloperCloudSError("requested_at must be timezone-aware")
    return parsed.isoformat()


def _validate_context(context: Any) -> None:
    if hasattr(context, "validate"):
        context.validate()


@dataclass(frozen=True)
class ProjectCreateRequest:
    project_id: str
    name: str
    description: str
    status: str
    settings: dict[str, Any] | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("project_id", self.project_id)
        _text("idempotency_key", self.idempotency_key)
        _text("name", self.name)
        _text("description", self.description)
        _text("status", self.status)

        settings = self.settings or {}
        if not isinstance(settings, dict):
            raise DeveloperCloudSError("settings must be a dict")

        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "settings": settings,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class EnvironmentCreateRequest:
    environment_id: str
    project_id: str
    name: str
    description: str
    status: str
    configuration: dict[str, Any] | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("environment_id", self.environment_id)
        _text("idempotency_key", self.idempotency_key)
        _text("project_id", self.project_id)
        _text("name", self.name)
        _text("description", self.description)
        _text("status", self.status)

        configuration = self.configuration or {}
        if not isinstance(configuration, dict):
            raise DeveloperCloudSError("configuration must be a dict")

        return {
            "environment_id": self.environment_id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "configuration": configuration,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class SDKCreateRequest:
    sdk_id: str
    name: str
    version: str
    language: str
    status: str
    repository_url: str
    documentation_url: str
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("sdk_id", self.sdk_id)
        _text("idempotency_key", self.idempotency_key)
        _text("name", self.name)
        _text("version", self.version)
        _text("language", self.language)
        _text("status", self.status)
        _text("repository_url", self.repository_url)
        _text("documentation_url", self.documentation_url)

        return {
            "sdk_id": self.sdk_id,
            "name": self.name,
            "version": self.version,
            "language": self.language,
            "status": self.status,
            "repository_url": self.repository_url,
            "documentation_url": self.documentation_url,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class DocumentationCreateRequest:
    documentation_id: str
    project_id: str
    title: str
    content: str
    version: str
    status: str
    tags: list[str] | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("documentation_id", self.documentation_id)
        _text("idempotency_key", self.idempotency_key)
        _text("project_id", self.project_id)
        _text("title", self.title)
        _text("content", self.content)
        _text("version", self.version)
        _text("status", self.status)

        tags = self.tags or []
        if not isinstance(tags, list):
            raise DeveloperCloudSError("tags must be a list")
        for tag in tags:
            if not isinstance(tag, str):
                raise DeveloperCloudSError("each tag must be a string")
            _text("tag", tag)

        return {
            "documentation_id": self.documentation_id,
            "project_id": self.project_id,
            "title": self.title,
            "content": self.content,
            "version": self.version,
            "status": self.status,
            "tags": tags,
            "requested_at": _time(self.requested_at),
        }


class DeveloperCloudService:
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
                    "data_classification": "DEVELOPER_CLOUD_PROJECT",
                },
            )
        )

    def plan_create_environment(
        self,
        *,
        context: Any,
        request: EnvironmentCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="ENVIRONMENT",
                entity_id=request.environment_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "DEVELOPER_CLOUD_ENVIRONMENT",
                },
            )
        )

    def plan_create_sdk(
        self,
        *,
        context: Any,
        request: SDKCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="SDK",
                entity_id=request.sdk_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "DEVELOPER_CLOUD_SDK",
                },
            )
        )

    def plan_create_documentation(
        self,
        *,
        context: Any,
        request: DocumentationCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="DOCUMENTATION",
                entity_id=request.documentation_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "DEVELOPER_CLOUD_DOCUMENTATION",
                },
            )
        )