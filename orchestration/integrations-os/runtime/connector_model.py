from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import re
from typing import Any


CANONICAL_CATEGORIES = {
    "Payments",
    "Banking",
    "Accounting",
    "Email",
    "SMS",
    "WhatsApp",
    "Logistics",
    "E-commerce",
    "Cloud",
    "Developer tools",
    "Analytics",
    "Government services",
    "IoT",
}

AUTH_METHODS = {
    "OAUTH",
    "API_KEY",
    "SERVICE_ACCOUNT",
    "WEBHOOK_SECRET",
    "NONE",
}

CIRCUIT_STATES = {
    "CLOSED",
    "OPEN",
    "HALF_OPEN",
}

SENSITIVE_FIELD_NAMES = {
    "access_token",
    "refresh_token",
    "api_key",
    "password",
    "secret",
    "client_secret",
    "private_key",
    "webhook_secret",
    "authorization",
    "cookie",
    "session_token",
}


class ConnectorValidationError(ValueError):
    pass


def _require_text(name: str, value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ConnectorValidationError(f"{name} must not be empty")
    return normalized


def _json_compatible(name: str, value: Any) -> None:
    try:
        json.dumps(value, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise ConnectorValidationError(
            f"{name} must be JSON-compatible"
        ) from exc


def _contains_sensitive_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).strip().lower() in SENSITIVE_FIELD_NAMES:
                return True
            if _contains_sensitive_key(item):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_sensitive_key(item) for item in value)
    return False


@dataclass
class CircuitBreakerPolicy:
    failure_threshold: int = 5
    recovery_timeout_seconds: int = 60
    half_open_max_calls: int = 1

    def validate(self) -> None:
        if self.failure_threshold < 1:
            raise ConnectorValidationError(
                "failure_threshold must be >= 1"
            )
        if self.recovery_timeout_seconds < 1:
            raise ConnectorValidationError(
                "recovery_timeout_seconds must be >= 1"
            )
        if self.half_open_max_calls < 1:
            raise ConnectorValidationError(
                "half_open_max_calls must be >= 1"
            )


@dataclass
class RateLimitPolicy:
    requests: int
    per_seconds: int

    def validate(self) -> None:
        if self.requests < 1:
            raise ConnectorValidationError("rate limit requests must be >= 1")
        if self.per_seconds < 1:
            raise ConnectorValidationError("rate limit window must be >= 1")


@dataclass
class ConnectorDefinition:
    connector_id: str
    name: str
    provider: str
    version: str
    owner: str
    category: str
    supported_auth_methods: list[str]
    supported_operations: list[str]
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    error_schema: dict[str, Any]
    rate_limit: RateLimitPolicy
    timeout_seconds: int = 30
    max_attempts: int = 3
    retryable_error_codes: list[str] = field(default_factory=list)
    idempotency_supported: bool = True
    circuit_breaker: CircuitBreakerPolicy = field(
        default_factory=CircuitBreakerPolicy
    )
    dead_letter_behavior: str = "LOOP_OS"
    secret_storage: str = "REFERENCE_ONLY"
    encryption_required: bool = True
    permission_scopes: list[str] = field(default_factory=list)
    audit_required: bool = True
    health_check: str = "DECLARED"
    metrics: bool = True
    logs: bool = True
    alerting: bool = True
    compatible_versions: list[str] = field(default_factory=list)
    credential_reference_required: bool = True
    webhook_secret_reference_required: bool = False
    enabled: bool = True

    def validate(self) -> None:
        self.connector_id = _require_text(
            "connector_id",
            self.connector_id,
        )
        self.name = _require_text("name", self.name)
        self.provider = _require_text("provider", self.provider)
        self.version = _require_text("version", self.version)
        self.owner = _require_text("owner", self.owner)

        if self.category not in CANONICAL_CATEGORIES:
            raise ConnectorValidationError(
                f"unsupported connector category: {self.category}"
            )

        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", self.connector_id):
            raise ConnectorValidationError(
                "connector_id must be lowercase slug-like text"
            )

        if not self.supported_operations:
            raise ConnectorValidationError(
                "supported_operations must not be empty"
            )

        if len(set(self.supported_operations)) != len(
            self.supported_operations
        ):
            raise ConnectorValidationError(
                "supported_operations contains duplicates"
            )

        auth_methods = [
            str(value).strip().upper()
            for value in self.supported_auth_methods
        ]

        invalid_auth = sorted(set(auth_methods) - AUTH_METHODS)
        if invalid_auth:
            raise ConnectorValidationError(
                "unsupported auth methods: " + ", ".join(invalid_auth)
            )

        if not auth_methods:
            raise ConnectorValidationError(
                "supported_auth_methods must not be empty"
            )

        self.supported_auth_methods = auth_methods

        if self.timeout_seconds < 1:
            raise ConnectorValidationError(
                "timeout_seconds must be >= 1"
            )

        if self.max_attempts < 1:
            raise ConnectorValidationError(
                "max_attempts must be >= 1"
            )

        if self.secret_storage != "REFERENCE_ONLY":
            raise ConnectorValidationError(
                "P0 secret_storage must be REFERENCE_ONLY"
            )

        if not self.encryption_required:
            raise ConnectorValidationError(
                "encryption_required must remain true"
            )

        if self.dead_letter_behavior != "LOOP_OS":
            raise ConnectorValidationError(
                "dead_letter_behavior must delegate to LOOP_OS"
            )

        for name, value in [
            ("input_schema", self.input_schema),
            ("output_schema", self.output_schema),
            ("error_schema", self.error_schema),
        ]:
            _json_compatible(name, value)
            if _contains_sensitive_key(value):
                raise ConnectorValidationError(
                    f"{name} contains a sensitive field name"
                )

        self.rate_limit.validate()
        self.circuit_breaker.validate()

        if not self.compatible_versions:
            self.compatible_versions = [self.version]

        if self.version not in self.compatible_versions:
            self.compatible_versions.append(self.version)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)
