from __future__ import annotations

from dataclasses import dataclass, field, asdict
from hashlib import sha256
import json
import re
from typing import Any


CATEGORIES = {
    "VALIDATION",
    "AUTHENTICATION",
    "AUTHORIZATION",
    "TENANCY",
    "CONFLICT",
    "NOT_FOUND",
    "RATE_LIMIT",
    "DEPENDENCY",
    "INTERNAL",
}

SENSITIVE_KEYS = {
    "authorization",
    "access_token",
    "refresh_token",
    "api_key",
    "password",
    "secret",
    "client_secret",
    "private_key",
    "cookie",
    "session_token",
    "webhook_secret",
    "card_number",
    "cvv",
    "cvc",
    "pan",
}


class KernelErrorContractError(ValueError):
    pass


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if str(key).strip().lower() in SENSITIVE_KEYS:
                result[key] = "[REDACTED]"
            else:
                result[key] = redact(item)
        return result

    if isinstance(value, list):
        return [redact(item) for item in value]

    if isinstance(value, tuple):
        return [redact(item) for item in value]

    return value


@dataclass(frozen=True)
class ErrorEnvelope:
    error_id: str
    code: str
    category: str
    message: str
    retryable: bool
    correlation_id: str
    details: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,63}", self.code):
            raise KernelErrorContractError(
                "code must be stable uppercase machine-readable text"
            )

        if self.category not in CATEGORIES:
            raise KernelErrorContractError(
                f"unsupported error category: {self.category}"
            )

        if not self.message.strip():
            raise KernelErrorContractError(
                "safe error message must not be empty"
            )

        if not self.correlation_id.strip():
            raise KernelErrorContractError(
                "correlation_id must not be empty"
            )

        try:
            json.dumps(
                self.details,
                sort_keys=True,
                separators=(",", ":"),
            )
        except (TypeError, ValueError) as exc:
            raise KernelErrorContractError(
                "error details must be JSON-compatible"
            ) from exc

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        data = asdict(self)
        data["details"] = redact(self.details)
        return data


def create_error(
    *,
    code: str,
    category: str,
    message: str,
    retryable: bool,
    correlation_id: str,
    details: dict[str, Any] | None = None,
) -> ErrorEnvelope:
    material = {
        "code": code,
        "category": category,
        "correlation_id": correlation_id,
    }
    digest = sha256(
        json.dumps(
            material,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    envelope = ErrorEnvelope(
        error_id="err_" + digest[:24],
        code=code,
        category=category,
        message=message,
        retryable=bool(retryable),
        correlation_id=correlation_id,
        details=redact(details or {}),
    )
    envelope.validate()
    return envelope


def normalize_exception(
    *,
    exc: Exception,
    correlation_id: str,
    code: str = "KERNEL_INTERNAL_ERROR",
) -> ErrorEnvelope:
    # Exception message and traceback are deliberately not exposed.
    return create_error(
        code=code,
        category="INTERNAL",
        message="Kernel operation failed safely",
        retryable=False,
        correlation_id=correlation_id,
        details={
            "exception_type": exc.__class__.__name__,
        },
    )
