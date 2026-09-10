from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Any, Dict, List, Optional, Union


class AIPrimitiveError(ValueError):
    pass


def _require_text(name: str, value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise AIPrimitiveError(
            f"{name} must not be empty"
        )
    return normalized


def validate_currency(currency: str) -> str:
    value = str(currency).strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", value):
        raise AIPrimitiveError(
            "currency must be three uppercase letters"
        )
    return value


@dataclass(frozen=True)
class Money:
    amount_minor: int
    currency: str

    def validate(self, *, allow_negative: bool = False) -> None:
        if not isinstance(self.amount_minor, int):
            raise AIPrimitiveError(
                "amount_minor must be an integer"
            )
        if not allow_negative and self.amount_minor < 0:
            raise AIPrimitiveError(
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
class AIResource:
    id: str
    entity_type: str
    tenant: TenantScope
    created_at: str
    updated_at: str

    def validate(self) -> None:
        _require_text("id", self.id)

        if self.entity_type not in AI_ENTITY_TYPES:
            raise AIPrimitiveError(
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
                raise AIPrimitiveError(
                    f"{name} must be ISO-8601"
                ) from exc


# Entity types for AI
AI_ENTITY_TYPES = {
    "MODEL",
    "PROMPT",
    "INFERENCE",
    "EMBEDDING",
}


@dataclass(frozen=True)
class Model:
    resource: AIResource
    name: str
    architecture: str  # e.g., "TRANSFORMER", "CNN", "RNN"
    version: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    is_public: bool = False

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "MODEL":
            raise AIPrimitiveError(
                "resource entity_type must be MODEL"
            )
        _require_text("name", self.name)
        _require_text("architecture", self.architecture)
        _require_text("version", self.version)
        if not isinstance(self.parameters, dict):
            raise AIPrimitiveError(
                "parameters must be a dict"
            )
        if not isinstance(self.is_active, bool):
            raise AIPrimitiveError(
                "is_active must be a boolean"
            )
        if not isinstance(self.is_public, bool):
            raise AIPrimitiveError(
                "is_public must be a boolean"
            )


@dataclass(frozen=True)
class Prompt:
    resource: AIResource
    name: str
    template: str
    variables: List[str] = field(default_factory=list)
    is_active: bool = True

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "PROMPT":
            raise AIPrimitiveError(
                "resource entity_type must be PROMPT"
            )
        _require_text("name", self.name)
        _require_text("template", self.template)
        if not isinstance(self.variables, list):
            raise AIPrimitiveError(
                "variables must be a list"
            )
        for var in self.variables:
            if not isinstance(var, str):
                raise AIPrimitiveError(
                    "each variable must be a string"
                )
            _require_text("variable", var)
        if not isinstance(self.is_active, bool):
            raise AIPrimitiveError(
                "is_active must be a boolean"
            )


@dataclass(frozen=True)
class Inference:
    resource: AIResource
    model_id: str
    prompt_id: str | None = None
    input: Union[str, Dict[str, Any]]
    output: Union[str, Dict[str, Any]] | None = None
    status: str  # e.g., "PENDING", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED"
    started_at: str | None = None
    completed_at: str | None = None
    tokens_used: int | None = None
    cost: Money | None = None
    error: str | None = None

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "INFERENCE":
            raise AIPrimitiveError(
                "resource entity_type must be INFERENCE"
            )
        _require_text("model_id", self.model_id)
        if self.prompt_id is not None:
            _require_text("prompt_id", self.prompt_id)
        if not isinstance(self.input, (str, dict)):
            raise AIPrimitiveError(
                "input must be a string or dict"
            )
        if self.output is not None and not isinstance(self.output, (str, dict)):
            raise AIPrimitiveError(
                "output must be a string or dict or None"
            )
        _require_text("status", self.status)
        if self.started_at is not None:
            try:
                datetime.fromisoformat(self.started_at)
            except ValueError as exc:
                raise AIPrimitiveError(
                    "started_at must be ISO-8601"
                ) from exc
        if self.completed_at is not None:
            try:
                datetime.fromisoformat(self.completed_at)
            except ValueError as exc:
                raise AIPrimitiveError(
                    "completed_at must be ISO-8601"
                ) from exc
        if self.tokens_used is not None:
            if not isinstance(self.tokens_used, int) or self.tokens_used < 0:
                raise AIPrimitiveError(
                    "tokens_used must be a non-negative integer"
                )
        if self.cost is not None:
            self.cost.validate()
        if self.error is not None and len(self.error) > 2000:
            raise AIPrimitiveError(
                "error must not exceed 2000 characters"
            )


@dataclass(frozen=True)
class Embedding:
    resource: AIResource
    model_id: str
    input: Union[str, List[str]]
    output: List[List[float]]  # list of embeddings, each embedding is a list of floats
    status: str  # e.g., "PENDING", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED"
    started_at: str | None = None
    completed_at: str | None = None
    tokens_used: int | None = None
    cost: Money | None = None
    error: str | None = None

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "EMBEDDING":
            raise AIPrimitiveError(
                "resource entity_type must be EMBEDDING"
            )
        _require_text("model_id", self.model_id)
        if not isinstance(self.input, (str, list)):
            raise AIPrimitiveError(
                "input must be a string or list of strings"
            )
        if isinstance(self.input, list):
            for item in self.input:
                if not isinstance(item, str):
                    raise AIPrimitiveError(
                        "each input item must be a string"
                    )
        if not isinstance(self.output, list):
            raise AIPrimitiveError(
                "output must be a list"
            )
        for emb in self.output:
            if not isinstance(emb, list):
                raise AIPrimitiveError(
                    "each embedding must be a list of floats"
                )
            for val in emb:
                if not isinstance(val, (int, float)):
                    raise AIPrimitiveError(
                        "each embedding value must be a number"
                    )
        _require_text("status", self.status)
        if self.started_at is not None:
            try:
                datetime.fromisoformat(self.started_at)
            except ValueError as exc:
                raise AIPrimitiveError(
                    "started_at must be ISO-8601"
                ) from exc
        if self.completed_at is not None:
            try:
                datetime.fromisoformat(self.completed_at)
            except ValueError as exc:
                raise AIPrimitiveError(
                    "completed_at must be ISO-8601"
                ) from exc
        if self.tokens_used is not None:
            if not isinstance(self.tokens_used, int) or self.tokens_used < 0:
                raise AIPrimitiveError(
                    "tokens_used must be a non-negative integer"
                )
        if self.cost is not None:
            self.cost.validate()
        if self.error is not None and len(self.error) > 2000:
            raise AIPrimitiveError(
                "error must not exceed 2000 characters"
            )