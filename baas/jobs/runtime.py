from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import re
from typing import Any


JOB_MODES = {
    "QUEUED",
    "DELAYED",
    "SCHEDULED",
}

JOB_STATES = {
    "QUEUED",
    "DELAYED",
    "SCHEDULED",
    "DISPATCHED",
    "RETRY_PENDING",
    "COMPLETED",
    "DEAD_LETTER",
    "CANCELLED",
}

TERMINAL_STATES = {
    "COMPLETED",
    "DEAD_LETTER",
    "CANCELLED",
}

HANDLER_REF_PATTERN = re.compile(
    r"(?:function|internal)://[A-Za-z0-9._~:/-]+"
)

SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "access_token",
    "refresh_token",
    "api_key",
    "password",
    "secret",
    "secret_value",
    "client_secret",
    "private_key",
    "session_token",
    "webhook_secret",
    "provider_credentials",
}


class JobsBaaSError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    result = str(value).strip()
    if not result:
        raise JobsBaaSError(
            f"{name} must not be empty"
        )
    return result


def _time(value: str | None = None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise JobsBaaSError(
            "timestamp must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise JobsBaaSError(
            "timestamp must be timezone-aware"
        )

    return parsed


def _contains_sensitive(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).strip().lower() in SENSITIVE_KEYS:
                return True
            if _contains_sensitive(item):
                return True
    elif isinstance(value, (list, tuple)):
        return any(
            _contains_sensitive(item)
            for item in value
        )
    return False


def _validate_json_metadata(
    value: dict[str, Any],
) -> None:
    try:
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise JobsBaaSError(
            "payload_metadata must be JSON-compatible"
        ) from exc

    if _contains_sensitive(value):
        raise JobsBaaSError(
            "payload_metadata contains secret-bearing fields"
        )


def _canonical_payload(
    value: dict[str, Any],
) -> str:
    _validate_json_metadata(value)

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


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
            _text(name, value)


@dataclass(frozen=True)
class JobDefinition:
    definition_id: str
    tenant: TenantScope
    job_type: str
    handler_ref: str
    timeout_seconds: int
    max_attempts: int
    queue_name: str
    enabled: bool = True

    def validate(self) -> None:
        _text(
            "definition_id",
            self.definition_id,
        )
        self.tenant.validate()

        if not re.fullmatch(
            r"[a-z0-9][a-z0-9._-]{2,127}",
            _text("job_type", self.job_type),
        ):
            raise JobsBaaSError(
                "job_type must be a safe identifier"
            )

        if not HANDLER_REF_PATTERN.fullmatch(
            str(self.handler_ref).strip()
        ):
            raise JobsBaaSError(
                "handler_ref must use function:// or internal://"
            )

        if (
            not isinstance(
                self.timeout_seconds,
                int,
            )
            or self.timeout_seconds < 1
            or self.timeout_seconds > 3600
        ):
            raise JobsBaaSError(
                "timeout_seconds must be 1..3600"
            )

        if (
            not isinstance(
                self.max_attempts,
                int,
            )
            or self.max_attempts < 1
            or self.max_attempts > 25
        ):
            raise JobsBaaSError(
                "max_attempts must be 1..25"
            )

        if not re.fullmatch(
            r"[a-z0-9][a-z0-9._-]{1,63}",
            _text(
                "queue_name",
                self.queue_name,
            ),
        ):
            raise JobsBaaSError(
                "queue_name must be a safe identifier"
            )


@dataclass(frozen=True)
class JobSubmission:
    submission_id: str
    definition_id: str
    idempotency_key: str
    mode: str
    payload_metadata: dict[str, Any]
    requested_at: str
    available_at: str | None = None
    schedule_expression: str | None = None

    def validate(self) -> None:
        _text(
            "submission_id",
            self.submission_id,
        )
        _text(
            "definition_id",
            self.definition_id,
        )
        _text(
            "idempotency_key",
            self.idempotency_key,
        )

        mode = str(
            self.mode
        ).strip().upper()

        if mode not in JOB_MODES:
            raise JobsBaaSError(
                f"unsupported job mode: {mode}"
            )

        _validate_json_metadata(
            self.payload_metadata
        )

        requested = _time(
            self.requested_at
        )

        if mode == "QUEUED":
            if self.schedule_expression:
                raise JobsBaaSError(
                    "QUEUED job may not define schedule_expression"
                )

        if mode == "DELAYED":
            if self.available_at is None:
                raise JobsBaaSError(
                    "DELAYED job requires available_at"
                )

            available = _time(
                self.available_at
            )

            if available <= requested:
                raise JobsBaaSError(
                    "DELAYED available_at must be after requested_at"
                )

            if self.schedule_expression:
                raise JobsBaaSError(
                    "DELAYED job may not define schedule_expression"
                )

        if mode == "SCHEDULED":
            _text(
                "schedule_expression",
                self.schedule_expression,
            )

            if self.available_at is None:
                raise JobsBaaSError(
                    "SCHEDULED job requires available_at"
                )

            available = _time(
                self.available_at
            )

            if available < requested:
                raise JobsBaaSError(
                    "SCHEDULED available_at may not precede requested_at"
                )


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    submission_id: str
    definition_id: str
    tenant: TenantScope
    job_type: str
    handler_ref: str
    idempotency_key: str
    payload_hash: str
    payload_metadata: dict[str, Any]
    state: str
    attempt: int
    max_attempts: int
    timeout_seconds: int
    queue_name: str
    available_at: str
    schedule_expression: str | None
    correlation_id: str
    kernel_authorization_ref: str
    last_error_code: str | None
    created_at: str
    updated_at: str

    def validate(self) -> None:
        for name, value in {
            "job_id": self.job_id,
            "submission_id": self.submission_id,
            "definition_id": self.definition_id,
            "job_type": self.job_type,
            "handler_ref": self.handler_ref,
            "idempotency_key": self.idempotency_key,
            "payload_hash": self.payload_hash,
            "queue_name": self.queue_name,
            "correlation_id": self.correlation_id,
            "kernel_authorization_ref": self.kernel_authorization_ref,
        }.items():
            _text(name, value)

        self.tenant.validate()

        if self.state not in JOB_STATES:
            raise JobsBaaSError(
                f"invalid job state: {self.state}"
            )

        if (
            not isinstance(self.attempt, int)
            or self.attempt < 0
            or self.attempt > self.max_attempts
        ):
            raise JobsBaaSError(
                "attempt must be within 0..max_attempts"
            )

        if not re.fullmatch(
            r"[a-f0-9]{64}",
            self.payload_hash,
        ):
            raise JobsBaaSError(
                "payload_hash must be SHA-256 hex"
            )

        _validate_json_metadata(
            self.payload_metadata
        )
        _time(self.available_at)
        _time(self.created_at)
        _time(self.updated_at)


@dataclass(frozen=True)
class LoopDispatchPlan:
    job_id: str
    job_type: str
    handler_ref: str
    attempt: int
    timeout_seconds: int
    queue_name: str
    tenant_context: dict[str, str]
    correlation_id: str
    idempotency_key: str
    kernel_authorization_ref: str
    pillars_approval_ref: str
    payload_metadata: dict[str, Any]
    audit_event: dict[str, Any]
    log_context: dict[str, Any]
    dispatch_state: str = "READY_FOR_LOOP_OS_ADAPTER"


class BackgroundJobsManager:
    def __init__(self) -> None:
        self._definitions: dict[
            str,
            JobDefinition,
        ] = {}
        self._jobs: dict[
            str,
            JobRecord,
        ] = {}
        self._idempotency: dict[
            tuple[str, str, str],
            tuple[str, str],
        ] = {}

    @staticmethod
    def _validate_request_context(
        request_context: Any,
    ) -> None:
        if hasattr(
            request_context,
            "validate",
        ):
            request_context.validate()

        for name in [
            "organization_id",
            "workspace_id",
            "project_id",
            "environment_id",
            "kernel_authorization_ref",
            "correlation_id",
            "actor_id",
        ]:
            _text(
                name,
                getattr(
                    request_context,
                    name,
                    None,
                ),
            )

        if not str(
            request_context.kernel_authorization_ref
        ).startswith("kernel_auth_"):
            raise JobsBaaSError(
                "job operations require Kernel authorization evidence"
            )

    @staticmethod
    def _same_tenant(
        tenant: TenantScope,
        request_context: Any,
    ) -> bool:
        return (
            tenant.organization_id
            == request_context.organization_id
            and tenant.workspace_id
            == request_context.workspace_id
            and tenant.project_id
            == request_context.project_id
            and tenant.environment_id
            == request_context.environment_id
        )

    def register_definition(
        self,
        *,
        definition: JobDefinition,
        request_context: Any,
    ) -> None:
        self._validate_request_context(
            request_context
        )
        definition.validate()

        if not self._same_tenant(
            definition.tenant,
            request_context,
        ):
            raise JobsBaaSError(
                "job definition tenant scope mismatch"
            )

        if (
            definition.definition_id
            in self._definitions
        ):
            raise JobsBaaSError(
                "job definition already registered"
            )

        self._definitions[
            definition.definition_id
        ] = definition

    def submit(
        self,
        *,
        submission: JobSubmission,
        request_context: Any,
    ) -> JobRecord:
        self._validate_request_context(
            request_context
        )
        submission.validate()

        definition = self._definitions.get(
            submission.definition_id
        )

        if definition is None:
            raise JobsBaaSError(
                "job definition not found"
            )

        if not definition.enabled:
            raise JobsBaaSError(
                "job definition is disabled"
            )

        if not self._same_tenant(
            definition.tenant,
            request_context,
        ):
            raise JobsBaaSError(
                "cross-tenant job submission denied"
            )

        payload_json = _canonical_payload(
            submission.payload_metadata
        )
        payload_hash = sha256(
            payload_json.encode("utf-8")
        ).hexdigest()

        idem_key = (
            request_context.organization_id,
            definition.definition_id,
            submission.idempotency_key,
        )

        existing = self._idempotency.get(
            idem_key
        )

        if existing is not None:
            existing_hash, job_id = existing

            if existing_hash != payload_hash:
                raise JobsBaaSError(
                    "idempotency key reused with different payload"
                )

            return self._jobs[
                job_id
            ]

        material = json.dumps(
            {
                "organization_id": (
                    request_context.organization_id
                ),
                "definition_id": (
                    definition.definition_id
                ),
                "idempotency_key": (
                    submission.idempotency_key
                ),
                "payload_hash": payload_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        job_id = (
            "job_"
            + sha256(
                material
            ).hexdigest()[:24]
        )

        mode = str(
            submission.mode
        ).strip().upper()

        if mode == "QUEUED":
            state = "QUEUED"
            available_at = (
                submission.requested_at
            )
        elif mode == "DELAYED":
            state = "DELAYED"
            available_at = _text(
                "available_at",
                submission.available_at,
            )
        else:
            state = "SCHEDULED"
            available_at = _text(
                "available_at",
                submission.available_at,
            )

        record = JobRecord(
            job_id=job_id,
            submission_id=(
                submission.submission_id
            ),
            definition_id=(
                definition.definition_id
            ),
            tenant=definition.tenant,
            job_type=definition.job_type,
            handler_ref=(
                definition.handler_ref
            ),
            idempotency_key=(
                submission.idempotency_key
            ),
            payload_hash=payload_hash,
            payload_metadata=dict(
                submission.payload_metadata
            ),
            state=state,
            attempt=0,
            max_attempts=(
                definition.max_attempts
            ),
            timeout_seconds=(
                definition.timeout_seconds
            ),
            queue_name=(
                definition.queue_name
            ),
            available_at=available_at,
            schedule_expression=(
                submission.schedule_expression
            ),
            correlation_id=(
                request_context.correlation_id
            ),
            kernel_authorization_ref=(
                request_context.kernel_authorization_ref
            ),
            last_error_code=None,
            created_at=(
                submission.requested_at
            ),
            updated_at=(
                submission.requested_at
            ),
        )
        record.validate()

        self._jobs[
            job_id
        ] = record
        self._idempotency[
            idem_key
        ] = (
            payload_hash,
            job_id,
        )

        return record

    def get(
        self,
        *,
        job_id: str,
        request_context: Any,
    ) -> JobRecord:
        self._validate_request_context(
            request_context
        )

        record = self._jobs.get(
            str(job_id).strip()
        )

        if record is None:
            raise JobsBaaSError(
                "job not found"
            )

        if not self._same_tenant(
            record.tenant,
            request_context,
        ):
            raise JobsBaaSError(
                "cross-tenant job access denied"
            )

        return record

    def build_dispatch_plan(
        self,
        *,
        job_id: str,
        pillars_approval_ref: str,
        request_context: Any,
        now: str | None = None,
    ) -> LoopDispatchPlan:
        record = self.get(
            job_id=job_id,
            request_context=request_context,
        )

        approval_ref = _text(
            "pillars_approval_ref",
            pillars_approval_ref,
        )

        if not approval_ref.startswith(
            "pillars_"
        ):
            raise JobsBaaSError(
                "pillars_approval_ref is invalid"
            )

        if (
            request_context.kernel_authorization_ref
            != record.kernel_authorization_ref
        ):
            raise JobsBaaSError(
                "Kernel authorization evidence changed after submission"
            )

        if record.state in TERMINAL_STATES:
            raise JobsBaaSError(
                "terminal job cannot be dispatched"
            )

        if record.state == "DISPATCHED":
            raise JobsBaaSError(
                "job is already dispatched"
            )

        current = _time(now)

        if current < _time(
            record.available_at
        ):
            raise JobsBaaSError(
                "job is not ready"
            )

        next_attempt = (
            record.attempt + 1
        )

        if next_attempt > record.max_attempts:
            raise JobsBaaSError(
                "job attempts exhausted"
            )

        updated = replace(
            record,
            state="DISPATCHED",
            attempt=next_attempt,
            updated_at=(
                current.isoformat()
            ),
        )
        updated.validate()

        self._jobs[
            job_id
        ] = updated

        return LoopDispatchPlan(
            job_id=updated.job_id,
            job_type=updated.job_type,
            handler_ref=(
                updated.handler_ref
            ),
            attempt=updated.attempt,
            timeout_seconds=(
                updated.timeout_seconds
            ),
            queue_name=(
                updated.queue_name
            ),
            tenant_context={
                "organization_id": (
                    updated.tenant.organization_id
                ),
                "workspace_id": (
                    updated.tenant.workspace_id
                ),
                "project_id": (
                    updated.tenant.project_id
                ),
                "environment_id": (
                    updated.tenant.environment_id
                ),
            },
            correlation_id=(
                updated.correlation_id
            ),
            idempotency_key=(
                updated.idempotency_key
            ),
            kernel_authorization_ref=(
                updated.kernel_authorization_ref
            ),
            pillars_approval_ref=(
                approval_ref
            ),
            payload_metadata=dict(
                updated.payload_metadata
            ),
            audit_event={
                "event_type": (
                    "baas.job.dispatch_planned"
                ),
                "job_id": (
                    updated.job_id
                ),
                "attempt": (
                    updated.attempt
                ),
                "organization_id": (
                    updated.tenant.organization_id
                ),
                "correlation_id": (
                    updated.correlation_id
                ),
                "kernel_authorization_ref": (
                    updated.kernel_authorization_ref
                ),
                "pillars_approval_ref": (
                    approval_ref
                ),
            },
            log_context={
                "job_id": (
                    updated.job_id
                ),
                "job_type": (
                    updated.job_type
                ),
                "attempt": (
                    updated.attempt
                ),
                "organization_id": (
                    updated.tenant.organization_id
                ),
                "correlation_id": (
                    updated.correlation_id
                ),
            },
        )

    def record_success(
        self,
        *,
        job_id: str,
        request_context: Any,
        now: str | None = None,
    ) -> JobRecord:
        record = self.get(
            job_id=job_id,
            request_context=request_context,
        )

        if record.state != "DISPATCHED":
            raise JobsBaaSError(
                "job must be DISPATCHED before success"
            )

        updated = replace(
            record,
            state="COMPLETED",
            last_error_code=None,
            updated_at=_time(
                now
            ).isoformat(),
        )

        self._jobs[
            job_id
        ] = updated

        return updated

    def record_failure(
        self,
        *,
        job_id: str,
        error_code: str,
        request_context: Any,
        now: str | None = None,
    ) -> JobRecord:
        record = self.get(
            job_id=job_id,
            request_context=request_context,
        )

        if record.state != "DISPATCHED":
            raise JobsBaaSError(
                "job must be DISPATCHED before failure"
            )

        code = _text(
            "error_code",
            error_code,
        )
        current = _time(
            now
        )

        if record.attempt >= record.max_attempts:
            updated = replace(
                record,
                state="DEAD_LETTER",
                last_error_code=code,
                updated_at=current.isoformat(),
            )
        else:
            backoff_seconds = min(
                30 * (
                    2 ** (
                        record.attempt - 1
                    )
                ),
                3600,
            )

            updated = replace(
                record,
                state="RETRY_PENDING",
                available_at=(
                    current
                    + timedelta(
                        seconds=backoff_seconds
                    )
                ).isoformat(),
                last_error_code=code,
                updated_at=current.isoformat(),
            )

        updated.validate()

        self._jobs[
            job_id
        ] = updated

        return updated

    def cancel(
        self,
        *,
        job_id: str,
        request_context: Any,
        now: str | None = None,
    ) -> JobRecord:
        record = self.get(
            job_id=job_id,
            request_context=request_context,
        )

        if record.state in TERMINAL_STATES:
            raise JobsBaaSError(
                "terminal job cannot be cancelled"
            )

        if record.state == "DISPATCHED":
            raise JobsBaaSError(
                "dispatched job requires runtime cancellation adapter"
            )

        updated = replace(
            record,
            state="CANCELLED",
            updated_at=_time(
                now
            ).isoformat(),
        )

        self._jobs[
            job_id
        ] = updated

        return updated

    def observation(
        self,
        *,
        job_id: str,
        request_context: Any,
    ) -> dict[str, Any]:
        record = self.get(
            job_id=job_id,
            request_context=request_context,
        )

        return {
            "job_id": record.job_id,
            "job_type": record.job_type,
            "state": record.state,
            "attempt": record.attempt,
            "max_attempts": (
                record.max_attempts
            ),
            "available_at": (
                record.available_at
            ),
            "last_error_code": (
                record.last_error_code
            ),
            "correlation_id": (
                record.correlation_id
            ),
            "updated_at": (
                record.updated_at
            ),
        }
