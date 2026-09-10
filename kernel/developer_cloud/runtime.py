from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Any, Dict, List, Optional, Union


class DeveloperCloudPrimitiveError(ValueError):
    pass


def _require_text(name: str, value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise DeveloperCloudPrimitiveError(
            f"{name} must not be empty"
        )
    return normalized


def validate_identifier(identifier: str) -> str:
    # Identifier should be alphanumeric with hyphens and underscores allowed, but not starting/ending with them
    value = str(identifier).strip()
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]", value):
        raise DeveloperCloudPrimitiveError(
            "identifier must be alphanumeric, can contain hyphens and underscores, but not start or end with them"
        )
    return value


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
class DeveloperCloudResource:
    id: str
    entity_type: str
    tenant: TenantScope
    created_at: str
    updated_at: str

    def validate(self) -> None:
        _require_text("id", self.id)

        if self.entity_type not in DEVELOPER_CLOUD_ENTITY_TYPES:
            raise DeveloperCloudPrimitiveError(
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
                raise DeveloperCloudPrimitiveError(
                    f"{name} must be ISO-8601"
                ) from exc


# Entity types for Developer Cloud
DEVELOPER_CLOUD_ENTITY_TYPES = {
    "PROJECT",
    "ENVIRONMENT",
    "SDK",
    "DOCUMENTATION",
}


@dataclass(frozen=True)
class Project:
    resource: DeveloperCloudResource
    name: str
    description: str
    status: str  # e.g., "ACTIVE", "ARCHIVED", "DELETED"
    settings: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "PROJECT":
            raise DeveloperCloudPrimitiveError(
                "resource entity_type must be PROJECT"
            )
        _require_text("name", self.name)
        _require_text("description", self.description)
        _require_text("status", self.status)
        if not isinstance(self.settings, dict):
            raise DeveloperCloudPrimitiveError(
                "settings must be a dict"
            )


@dataclass(frozen=True)
class Environment:
    resource: DeveloperCloudResource
    project_id: str
    name: str
    description: str
    status: str  # e.g., "ACTIVE", "INACTIVE", "DELETED"
    configuration: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "ENVIRONMENT":
            raise DeveloperCloudPrimitiveError(
                "resource entity_type must be ENVIRONMENT"
            )
        _require_text("project_id", self.project_id)
        _require_text("name", self.name)
        _require_text("description", self.description)
        _require_text("status", self.status)
        if not isinstance(self.configuration, dict):
            raise DeveloperCloudPrimitiveError(
                "configuration must be a dict"
            )


@dataclass(frozen=True)
class SDK:
    resource: DeveloperCloudResource
    name: str
    version: str
    language: str  # e.g., "PYTHON", "JAVASCRIPT", "JAVA"
    status: str  # e.g., "ACTIVE", "DEPRECATED", "RETIRED"
    repository_url: str
    documentation_url: str

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "SDK":
            raise DeveloperCloudPrimitiveError(
                "resource entity_type must be SDK"
            )
        _require_text("name", self.name)
        _require_text("version", self.version)
        _require_text("language", self.language)
        _require_text("status", self.status)
        _require_text("repository_url", self.repository_url)
        _require_text("documentation_url", self.documentation_url)


@dataclass(frozen=True)
class Documentation:
    resource: DeveloperCloudResource
    project_id: str
    title: str
    content: str
    version: str
    status: str  # e.g., "DRAFT", "PUBLISHED", "ARCHIVED"
    tags: List[str] = field(default_factory=list)

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "DOCUMENTATION":
            raise DeveloperCloudPrimitiveError(
                "resource entity_type must be DOCUMENTATION"
            )
        _require_text("project_id", self.project_id)
        _require_text("title", self.title)
        _require_text("content", self.content)
        _require_text("version", self.version)
        _require_text("status", self.status)
        if not isinstance(self.tags, list):
            raise DeveloperCloudPrimitiveError(
                "tags must be a list"
            )
        for tag in self.tags:
            if not isinstance(tag, str):
                raise DeveloperCloudPrimitiveError(
                    "each tag must be a string"
                )
            _require_text("tag", tag)