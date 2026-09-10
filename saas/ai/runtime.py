from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kernel.ai.runtime import (
    Model,
    Prompt,
    Inference,
    Embedding,
    AIPrimitiveError,
    Money,
    TenantScope,
    AIResource,
)


class AISError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise AISError(f"{name} must not be empty")
    result = str(value).strip()
    if not result:
        raise AISError(f"{name} must not be empty")
    return result


def _time(value: str | None = None) -> str:
    from datetime import datetime, timezone
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise AISError("requested_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise AISError("requested_at must be timezone-aware")
    return parsed.isoformat()


def _validate_context(context: Any) -> None:
    if hasattr(context, "validate"):
        context.validate()


@dataclass(frozen=True)
class ModelCreateRequest:
    model_id: str
    name: str
    architecture: str
    version: str
    parameters: dict[str, Any] | None = None
    is_active: bool | None = None
    is_public: bool | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("model_id", self.model_id)
        _text("idempotency_key", self.idempotency_key)
        _text("name", self.name)
        _text("architecture", self.architecture)
        _text("version", self.version)

        parameters = self.parameters or {}
        if not isinstance(parameters, dict):
            raise AISError("parameters must be a dict")

        is_active = self.is_active if self.is_active is not None else True
        if not isinstance(is_active, bool):
            raise AISError("is_active must be a boolean")

        is_public = self.is_public if self.is_public is not None else False
        if not isinstance(is_public, bool):
            raise AISError("is_public must be a boolean")

        return {
            "model_id": self.model_id,
            "name": self.name,
            "architecture": self.architecture,
            "version": self.version,
            "parameters": parameters,
            "is_active": is_active,
            "is_public": is_public,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class PromptCreateRequest:
    prompt_id: str
    name: str
    template: str
    variables: list[str] | None = None
    is_active: bool | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("prompt_id", self.prompt_id)
        _text("idempotency_key", self.idempotency_key)
        _text("name", self.name)
        _text("template", self.template)

        variables = self.variables or []
        if not isinstance(variables, list):
            raise AISError("variables must be a list")
        for var in variables:
            if not isinstance(var, str):
                raise AISError("each variable must be a string")
            _text("variable", var)

        is_active = self.is_active if self.is_active is not None else True
        if not isinstance(is_active, bool):
            raise AISError("is_active must be a boolean")

        return {
            "prompt_id": self.prompt_id,
            "name": self.name,
            "template": self.template,
            "variables": variables,
            "is_active": is_active,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class InferenceCreateRequest:
    inference_id: str
    model_id: str
    prompt_id: str | None = None
    input: Union[str, dict[str, Any]]
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("inference_id", self.inference_id)
        _text("idempotency_key", self.idempotency_key)
        _text("model_id", self.model_id)
        if self.prompt_id is not None:
            _text("prompt_id", self.prompt_id)
        if not isinstance(self.input, (str, dict)):
            raise AISError("input must be a string or dict")

        return {
            "inference_id": self.inference_id,
            "model_id": self.model_id,
            "prompt_id": self.prompt_id,
            "input": self.input,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class EmbeddingCreateRequest:
    embedding_id: str
    model_id: str
    input: Union[str, list[str]]
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("embedding_id", self.embedding_id)
        _text("idempotency_key", self.idempotency_key)
        _text("model_id", self.model_id)
        if not isinstance(self.input, (str, list)):
            raise AISError("input must be a string or list of strings")
        if isinstance(self.input, list):
            for item in self.input:
                if not isinstance(item, str):
                    raise AISError("each input item must be a string")

        return {
            "embedding_id": self.embedding_id,
            "model_id": self.model_id,
            "input": self.input,
            "requested_at": _time(self.requested_at),
        }


class AIService:
    def __init__(
        self,
        *,
        foundation: Any,
        product_command_type: Any,
    ) -> None:
        self._foundation = foundation
        self._product_command_type = product_command_type

    def plan_create_model(
        self,
        *,
        context: Any,
        request: ModelCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="MODEL",
                entity_id=request.model_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "AI_MODEL",
                },
            )
        )

    def plan_create_prompt(
        self,
        *,
        context: Any,
        request: PromptCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="PROMPT",
                entity_id=request.prompt_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "AI_PROMPT",
                },
            )
        )

    def plan_create_inference(
        self,
        *,
        context: Any,
        request: InferenceCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="INFERENCE",
                entity_id=request.inference_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "AI_INFERENCE",
                },
            )
        )

    def plan_create_embedding(
        self,
        *,
        context: Any,
        request: EmbeddingCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="EMBEDDING",
                entity_id=request.embedding_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "AI_EMBEDDING",
                },
            )
        )