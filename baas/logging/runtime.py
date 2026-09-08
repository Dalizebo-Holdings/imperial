from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from typing import Any, Callable


LEVEL_ORDER = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}

P0_SOURCE_SERVICES = {
    "authentication",
    "database",
    "storage",
    "functions",
    "api_gateway",
    "events",
    "webhooks",
    "background_jobs",
    "audit",
    "logging",
    "usage_metering",
    "subscription_billing",
    "payments",
    "secrets",
    "backups",
}


class LoggingBaaSError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    result = str(value).strip()
    if not result:
        raise LoggingBaaSError(
            f"{name} must not be empty"
        )
    return result


def _time(value: str | None = None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise LoggingBaaSError(
            "timestamp must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise LoggingBaaSError(
            "timestamp must be timezone-aware"
        )

    return parsed


def _canonical_size(value: dict[str, Any]) -> int:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise LoggingBaaSError(
            "log fields must be JSON-compatible"
        ) from exc

    return len(encoded)


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
class LogStreamPolicy:
    policy_id: str
    tenant: TenantScope
    minimum_level: str
    retention_days: int
    max_fields_bytes: int
    enabled: bool = True

    def validate(self) -> None:
        _text("policy_id", self.policy_id)
        self.tenant.validate()

        level = str(
            self.minimum_level
        ).strip().upper()

        if level not in LEVEL_ORDER:
            raise LoggingBaaSError(
                f"unsupported minimum_level: {level}"
            )

        if (
            not isinstance(self.retention_days, int)
            or self.retention_days < 1
            or self.retention_days > 3650
        ):
            raise LoggingBaaSError(
                "retention_days must be 1..3650"
            )

        if (
            not isinstance(self.max_fields_bytes, int)
            or self.max_fields_bytes < 256
            or self.max_fields_bytes > 65536
        ):
            raise LoggingBaaSError(
                "max_fields_bytes must be 256..65536"
            )


@dataclass(frozen=True)
class LogIngestRequest:
    source_service: str
    level: str
    event: str
    correlation_id: str
    fields: dict[str, Any]
    timestamp: str
    actor_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None

    def validate(self) -> None:
        service = _text(
            "source_service",
            self.source_service,
        )

        if service not in P0_SOURCE_SERVICES:
            raise LoggingBaaSError(
                f"unsupported source_service: {service}"
            )

        level = str(
            self.level
        ).strip().upper()

        if level not in LEVEL_ORDER:
            raise LoggingBaaSError(
                f"unsupported log level: {level}"
            )

        _text("event", self.event)
        _text(
            "correlation_id",
            self.correlation_id,
        )
        _time(self.timestamp)

        if self.actor_id is not None:
            _text("actor_id", self.actor_id)

        if self.trace_id is not None:
            _text("trace_id", self.trace_id)

        if self.span_id is not None:
            _text("span_id", self.span_id)

        _canonical_size(
            self.fields
        )


@dataclass(frozen=True)
class LogQuery:
    minimum_level: str | None = None
    source_service: str | None = None
    event_prefix: str | None = None
    actor_id: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    timestamp_from: str | None = None
    timestamp_to: str | None = None
    after_sequence: int = 0
    limit: int = 100

    def validate(self) -> None:
        if self.minimum_level is not None:
            level = str(
                self.minimum_level
            ).strip().upper()

            if level not in LEVEL_ORDER:
                raise LoggingBaaSError(
                    f"unsupported minimum_level: {level}"
                )

        if self.source_service is not None:
            service = _text(
                "source_service",
                self.source_service,
            )

            if service not in P0_SOURCE_SERVICES:
                raise LoggingBaaSError(
                    f"unsupported source_service: {service}"
                )

        if self.event_prefix is not None:
            _text(
                "event_prefix",
                self.event_prefix,
            )

        if (
            not isinstance(self.after_sequence, int)
            or self.after_sequence < 0
        ):
            raise LoggingBaaSError(
                "after_sequence must be an integer >= 0"
            )

        if (
            not isinstance(self.limit, int)
            or self.limit < 1
            or self.limit > 1000
        ):
            raise LoggingBaaSError(
                "limit must be 1..1000"
            )

        start = (
            _time(self.timestamp_from)
            if self.timestamp_from
            else None
        )
        end = (
            _time(self.timestamp_to)
            if self.timestamp_to
            else None
        )

        if (
            start is not None
            and end is not None
            and start > end
        ):
            raise LoggingBaaSError(
                "timestamp_from may not exceed timestamp_to"
            )


@dataclass(frozen=True)
class LogQueryResult:
    organization_id: str
    records: tuple[dict[str, Any], ...]
    next_after_sequence: int | None
    access_log_context: dict[str, Any]


class LoggingService:
    def __init__(
        self,
        *,
        kernel_emit: Callable[..., dict[str, Any]],
    ) -> None:
        if not callable(kernel_emit):
            raise LoggingBaaSError(
                "kernel_emit must be callable"
            )

        self._kernel_emit = kernel_emit
        self._policies: dict[
            tuple[str, str, str, str],
            LogStreamPolicy,
        ] = {}
        self._records: list[
            dict[str, Any]
        ] = []
        self._sequence = 0

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
            "request_id",
            "correlation_id",
            "service",
            "operation",
            "organization_id",
            "workspace_id",
            "project_id",
            "environment_id",
            "actor_id",
            "kernel_authorization_ref",
        ]:
            _text(
                name,
                getattr(
                    request_context,
                    name,
                    None,
                ),
            )

        if (
            str(
                request_context.service
            ).strip()
            != "logging"
        ):
            raise LoggingBaaSError(
                "LoggingService requires service=logging"
            )

        if not str(
            request_context.kernel_authorization_ref
        ).startswith("kernel_auth_"):
            raise LoggingBaaSError(
                "logging operations require Kernel authorization evidence"
            )

    @staticmethod
    def _scope_from_context(
        request_context: Any,
    ) -> TenantScope:
        scope = TenantScope(
            organization_id=(
                request_context.organization_id
            ),
            workspace_id=(
                request_context.workspace_id
            ),
            project_id=(
                request_context.project_id
            ),
            environment_id=(
                request_context.environment_id
            ),
        )
        scope.validate()
        return scope

    @staticmethod
    def _scope_key(
        tenant: TenantScope,
    ) -> tuple[str, str, str, str]:
        return (
            tenant.organization_id,
            tenant.workspace_id,
            tenant.project_id,
            tenant.environment_id,
        )

    def register_policy(
        self,
        *,
        policy: LogStreamPolicy,
        request_context: Any,
    ) -> None:
        self._validate_request_context(
            request_context
        )
        policy.validate()

        expected = (
            self._scope_from_context(
                request_context
            )
        )

        if self._scope_key(
            policy.tenant
        ) != self._scope_key(
            expected
        ):
            raise LoggingBaaSError(
                "log policy tenant scope mismatch"
            )

        key = self._scope_key(
            policy.tenant
        )

        if key in self._policies:
            raise LoggingBaaSError(
                "log policy already registered for tenant environment"
            )

        self._policies[key] = policy

    def _policy(
        self,
        request_context: Any,
    ) -> LogStreamPolicy:
        tenant = self._scope_from_context(
            request_context
        )

        policy = self._policies.get(
            self._scope_key(
                tenant
            )
        )

        if policy is None:
            raise LoggingBaaSError(
                "log stream policy not found"
            )

        if not policy.enabled:
            raise LoggingBaaSError(
                "log stream policy is disabled"
            )

        return policy

    def ingest(
        self,
        *,
        request: LogIngestRequest,
        request_context: Any,
    ) -> dict[str, Any]:
        self._validate_request_context(
            request_context
        )
        request.validate()
        policy = self._policy(
            request_context
        )

        if (
            request.correlation_id
            != request_context.correlation_id
        ):
            raise LoggingBaaSError(
                "log correlation_id must match request context"
            )

        if (
            request.actor_id is not None
            and request.actor_id
            != request_context.actor_id
        ):
            raise LoggingBaaSError(
                "log actor_id contradicts request context"
            )

        if (
            _canonical_size(
                request.fields
            )
            > policy.max_fields_bytes
        ):
            raise LoggingBaaSError(
                "log fields exceed policy size limit"
            )

        level = str(
            request.level
        ).strip().upper()

        minimum = str(
            policy.minimum_level
        ).strip().upper()

        if (
            LEVEL_ORDER[level]
            < LEVEL_ORDER[minimum]
        ):
            return {
                "accepted": False,
                "reason": "below_minimum_level",
            }

        kernel_record = self._kernel_emit(
            level=level,
            event=request.event,
            correlation_id=(
                request.correlation_id
            ),
            organization_id=(
                request_context.organization_id
            ),
            actor_id=(
                request.actor_id
                or request_context.actor_id
            ),
            trace_id=request.trace_id,
            span_id=request.span_id,
            fields=request.fields,
            timestamp=request.timestamp,
        )

        if not isinstance(
            kernel_record,
            dict,
        ):
            raise LoggingBaaSError(
                "Kernel logging sink returned invalid record"
            )

        required = {
            "timestamp",
            "level",
            "event",
            "correlation_id",
            "organization_id",
            "actor_id",
            "trace_id",
            "span_id",
            "fields",
        }

        if not required.issubset(
            kernel_record
        ):
            raise LoggingBaaSError(
                "Kernel logging record is missing required fields"
            )

        if (
            str(
                kernel_record[
                    "organization_id"
                ]
            )
            != request_context.organization_id
        ):
            raise LoggingBaaSError(
                "Kernel logging record tenant mismatch"
            )

        self._sequence += 1

        indexed = {
            "sequence": self._sequence,
            "source_service": (
                request.source_service
            ),
            **kernel_record,
        }

        self._records.append(
            indexed
        )

        return {
            "accepted": True,
            "sequence": (
                self._sequence
            ),
            "record": dict(
                indexed
            ),
        }

    def query(
        self,
        *,
        query: LogQuery,
        request_context: Any,
    ) -> LogQueryResult:
        self._validate_request_context(
            request_context
        )
        query.validate()
        self._policy(
            request_context
        )

        selected: list[
            dict[str, Any]
        ] = []

        for record in self._records:
            if (
                record[
                    "organization_id"
                ]
                != request_context.organization_id
            ):
                continue

            if (
                record["sequence"]
                <= query.after_sequence
            ):
                continue

            if (
                query.minimum_level
                is not None
                and LEVEL_ORDER[
                    str(
                        record[
                            "level"
                        ]
                    ).upper()
                ]
                < LEVEL_ORDER[
                    str(
                        query.minimum_level
                    ).upper()
                ]
            ):
                continue

            if (
                query.source_service
                is not None
                and record[
                    "source_service"
                ]
                != query.source_service
            ):
                continue

            if (
                query.event_prefix
                is not None
                and not str(
                    record[
                        "event"
                    ]
                ).startswith(
                    query.event_prefix
                )
            ):
                continue

            for field_name in [
                "actor_id",
                "correlation_id",
                "trace_id",
            ]:
                expected = getattr(
                    query,
                    field_name,
                )

                if (
                    expected is not None
                    and str(
                        record.get(
                            field_name
                        )
                    )
                    != str(expected)
                ):
                    break
            else:
                timestamp = _time(
                    str(
                        record[
                            "timestamp"
                        ]
                    )
                )

                if (
                    query.timestamp_from
                    and timestamp
                    < _time(
                        query.timestamp_from
                    )
                ):
                    continue

                if (
                    query.timestamp_to
                    and timestamp
                    > _time(
                        query.timestamp_to
                    )
                ):
                    continue

                selected.append(
                    dict(
                        record
                    )
                )

        selected.sort(
            key=lambda item: (
                item["sequence"]
            )
        )

        page = selected[
            : query.limit
        ]

        more = (
            len(selected)
            > len(page)
        )

        next_sequence = (
            page[-1]["sequence"]
            if more and page
            else None
        )

        return LogQueryResult(
            organization_id=(
                request_context.organization_id
            ),
            records=tuple(
                page
            ),
            next_after_sequence=(
                next_sequence
            ),
            access_log_context={
                "service": "logging",
                "operation": (
                    "logging.query"
                ),
                "request_id": (
                    request_context.request_id
                ),
                "correlation_id": (
                    request_context.correlation_id
                ),
                "organization_id": (
                    request_context.organization_id
                ),
                "selected_count": (
                    len(page)
                ),
            },
        )

    def retention_cutoff(
        self,
        *,
        request_context: Any,
        now: str | None = None,
    ) -> str:
        self._validate_request_context(
            request_context
        )
        policy = self._policy(
            request_context
        )

        cutoff = (
            _time(now)
            - timedelta(
                days=(
                    policy.retention_days
                )
            )
        )

        return cutoff.isoformat()
