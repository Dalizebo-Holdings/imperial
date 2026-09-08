from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from hashlib import sha256
import json
from typing import Any


STATUSES = {
    "CREATED",
    "QUEUED",
    "RUNNING",
    "COMPLETED",
    "FAILED",
    "RETRY_PENDING",
    "DEAD_LETTERED",
}

TERMINAL_STATUSES = {
    "COMPLETED",
    "DEAD_LETTERED",
}


class JobValidationError(ValueError):
    pass


def _require_text(name: str, value: str) -> str:
    normalized = str(value).strip()

    if not normalized:
        raise JobValidationError(f"{name} must not be empty")

    return normalized


def _validate_json_compatible(name: str, value: Any) -> None:
    try:
        json.dumps(value, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise JobValidationError(
            f"{name} must be JSON-compatible"
        ) from exc


@dataclass
class LoopJob:
    job_id: str
    organization_id: str
    workflow_id: str
    job_type: str
    status: str = "CREATED"
    attempt: int = 0
    max_attempts: int = 3
    scheduled_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    timeout: int = 300
    idempotency_key: str = ""
    correlation_id: str = ""
    payload: Any = field(default_factory=dict)
    result: Any = None
    error_code: str | None = None

    def validate(self) -> None:
        self.job_id = _require_text("job_id", self.job_id)
        self.organization_id = _require_text(
            "organization_id",
            self.organization_id,
        )
        self.workflow_id = _require_text(
            "workflow_id",
            self.workflow_id,
        )
        self.job_type = _require_text("job_type", self.job_type)
        self.idempotency_key = _require_text(
            "idempotency_key",
            self.idempotency_key,
        )
        self.correlation_id = _require_text(
            "correlation_id",
            self.correlation_id,
        )

        self.status = str(self.status).strip().upper()

        if self.status not in STATUSES:
            raise JobValidationError(
                f"invalid job status: {self.status}"
            )

        if not isinstance(self.attempt, int) or self.attempt < 0:
            raise JobValidationError(
                "attempt must be a non-negative integer"
            )

        if not isinstance(self.max_attempts, int) or self.max_attempts < 1:
            raise JobValidationError(
                "max_attempts must be an integer >= 1"
            )

        if self.attempt > self.max_attempts:
            raise JobValidationError(
                "attempt may not exceed max_attempts"
            )

        if not isinstance(self.timeout, int) or self.timeout <= 0:
            raise JobValidationError(
                "timeout must be a positive integer number of seconds"
            )

        _validate_json_compatible("payload", self.payload)
        _validate_json_compatible("result", self.result)

        for field_name in (
            "scheduled_at",
            "started_at",
            "completed_at",
        ):
            value = getattr(self, field_name)

            if value is not None:
                try:
                    datetime.fromisoformat(value)
                except ValueError as exc:
                    raise JobValidationError(
                        f"{field_name} must be ISO-8601 or null"
                    ) from exc

    @property
    def terminal(self) -> bool:
        return self.status in TERMINAL_STATUSES

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)

    def fingerprint(self) -> str:
        self.validate()

        material = {
            "organization_id": self.organization_id,
            "workflow_id": self.workflow_id,
            "job_type": self.job_type,
            "idempotency_key": self.idempotency_key,
            "payload": self.payload,
        }

        encoded = json.dumps(
            material,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

        return sha256(encoded).hexdigest()
