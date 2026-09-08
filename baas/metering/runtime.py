from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
from typing import Any


METRICS = {
    "api_requests",
    "database_storage",
    "database_compute",
    "object_storage",
    "bandwidth",
    "function_executions",
    "realtime_connections",
    "ai_usage",
    "vector_operations",
    "messaging_usage",
}

SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
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
    "card_number",
    "cvv",
    "cvc",
    "pan",
}

UNIT_PATTERN = re.compile(
    r"[a-z][a-z0-9._/-]{0,63}"
)

PRODUCER_PATTERN = re.compile(
    r"[a-z][a-z0-9._-]{1,63}"
)


class MeteringBaaSError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    result = str(value).strip()
    if not result:
        raise MeteringBaaSError(
            f"{name} must not be empty"
        )
    return result


def _time(
    value: str | None = None,
) -> datetime:
    if value is None:
        return datetime.now(
            timezone.utc
        )

    try:
        parsed = datetime.fromisoformat(
            value
        )
    except ValueError as exc:
        raise MeteringBaaSError(
            "timestamp must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise MeteringBaaSError(
            "timestamp must be timezone-aware"
        )

    return parsed


def _canonical_json(
    value: Any,
) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise MeteringBaaSError(
            "value must be JSON-compatible"
        ) from exc


def _contains_sensitive(
    value: Any,
) -> bool:
    if isinstance(
        value,
        dict,
    ):
        for key, item in value.items():
            if (
                str(key).strip().lower()
                in SENSITIVE_KEYS
            ):
                return True
            if _contains_sensitive(
                item
            ):
                return True

    elif isinstance(
        value,
        (list, tuple),
    ):
        return any(
            _contains_sensitive(item)
            for item in value
        )

    return False


def _validate_dimensions(
    value: dict[str, Any],
) -> None:
    encoded = _canonical_json(
        value
    ).encode("utf-8")

    if len(encoded) > 8192:
        raise MeteringBaaSError(
            "dimensions exceed 8192 bytes"
        )

    if _contains_sensitive(
        value
    ):
        raise MeteringBaaSError(
            "dimensions contain secret-bearing fields"
        )


def canonical_quantity(
    value: str,
) -> str:
    raw = _text(
        "quantity",
        value,
    )

    try:
        number = Decimal(
            raw
        )
    except InvalidOperation as exc:
        raise MeteringBaaSError(
            "quantity must be a decimal string"
        ) from exc

    if not number.is_finite():
        raise MeteringBaaSError(
            "quantity must be finite"
        )

    if number < 0:
        raise MeteringBaaSError(
            "quantity must be non-negative"
        )

    exponent = number.as_tuple().exponent

    if (
        isinstance(
            exponent,
            int,
        )
        and exponent < -18
    ):
        raise MeteringBaaSError(
            "quantity supports at most 18 fractional digits"
        )

    normalized = format(
        number,
        "f",
    )

    if "." in normalized:
        normalized = normalized.rstrip(
            "0"
        ).rstrip(".")

    return normalized or "0"


@dataclass(frozen=True)
class TenantScope:
    organization_id: str
    workspace_id: str
    project_id: str
    environment_id: str

    def validate(self) -> None:
        for name, value in {
            "organization_id": (
                self.organization_id
            ),
            "workspace_id": (
                self.workspace_id
            ),
            "project_id": (
                self.project_id
            ),
            "environment_id": (
                self.environment_id
            ),
        }.items():
            _text(
                name,
                value,
            )


@dataclass(frozen=True)
class UsageEvent:
    submission_id: str
    producer: str
    idempotency_key: str
    metric: str
    unit: str
    quantity: str
    occurred_at: str
    dimensions: dict[str, Any]
    source_ref: str

    def validate(self) -> None:
        _text(
            "submission_id",
            self.submission_id,
        )

        producer = _text(
            "producer",
            self.producer,
        )

        if not PRODUCER_PATTERN.fullmatch(
            producer
        ):
            raise MeteringBaaSError(
                "producer must be a safe identifier"
            )

        _text(
            "idempotency_key",
            self.idempotency_key,
        )

        metric = str(
            self.metric
        ).strip()

        if metric not in METRICS:
            raise MeteringBaaSError(
                f"unsupported metric: {metric}"
            )

        unit = str(
            self.unit
        ).strip()

        if not UNIT_PATTERN.fullmatch(
            unit
        ):
            raise MeteringBaaSError(
                "unit must be a safe unit identifier"
            )

        canonical_quantity(
            self.quantity
        )
        _time(
            self.occurred_at
        )
        _validate_dimensions(
            self.dimensions
        )
        _text(
            "source_ref",
            self.source_ref,
        )


@dataclass(frozen=True)
class UsageRecord:
    usage_id: str
    tenant: TenantScope
    producer: str
    idempotency_key: str
    metric: str
    unit: str
    quantity: str
    occurred_at: str
    dimensions: dict[str, Any]
    source_ref: str
    correlation_id: str
    actor_id: str
    kernel_authorization_ref: str
    record_hash: str
    ingested_at: str

    def validate(self) -> None:
        _text(
            "usage_id",
            self.usage_id,
        )
        self.tenant.validate()

        if self.metric not in METRICS:
            raise MeteringBaaSError(
                f"unsupported metric: {self.metric}"
            )

        if not UNIT_PATTERN.fullmatch(
            self.unit
        ):
            raise MeteringBaaSError(
                "invalid unit"
            )

        if (
            canonical_quantity(
                self.quantity
            )
            != self.quantity
        ):
            raise MeteringBaaSError(
                "usage quantity is not canonical"
            )

        _time(
            self.occurred_at
        )
        _time(
            self.ingested_at
        )
        _validate_dimensions(
            self.dimensions
        )

        if not re.fullmatch(
            r"[a-f0-9]{64}",
            self.record_hash,
        ):
            raise MeteringBaaSError(
                "record_hash must be SHA-256 hex"
            )


@dataclass(frozen=True)
class UsageAggregate:
    aggregate_id: str
    tenant: TenantScope
    metric: str
    unit: str
    total_quantity: str
    event_count: int
    period_start: str
    period_end: str
    source_hash: str
    source_usage_ids: tuple[
        str,
        ...
    ]
    generated_at: str
    audit_event: dict[str, Any]


class UsageMeteringService:
    def __init__(
        self,
    ) -> None:
        self._records: dict[
            str,
            UsageRecord,
        ] = {}
        self._idempotency: dict[
            tuple[
                str,
                str,
                str,
                str,
            ],
            tuple[
                str,
                str,
            ],
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
            != "usage_metering"
        ):
            raise MeteringBaaSError(
                "UsageMeteringService requires service=usage_metering"
            )

        if not str(
            request_context.kernel_authorization_ref
        ).startswith(
            "kernel_auth_"
        ):
            raise MeteringBaaSError(
                "usage metering requires Kernel authorization evidence"
            )

    @staticmethod
    def _tenant_from_context(
        request_context: Any,
    ) -> TenantScope:
        tenant = TenantScope(
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
        tenant.validate()
        return tenant

    @staticmethod
    def _tenant_equal(
        left: TenantScope,
        right: TenantScope,
    ) -> bool:
        return (
            left.organization_id
            == right.organization_id
            and left.workspace_id
            == right.workspace_id
            and left.project_id
            == right.project_id
            and left.environment_id
            == right.environment_id
        )

    def ingest(
        self,
        *,
        event: UsageEvent,
        request_context: Any,
        ingested_at: str | None = None,
    ) -> dict[str, Any]:
        self._validate_request_context(
            request_context
        )
        event.validate()

        tenant = self._tenant_from_context(
            request_context
        )

        quantity = canonical_quantity(
            event.quantity
        )

        canonical_event = {
            "organization_id": (
                tenant.organization_id
            ),
            "workspace_id": (
                tenant.workspace_id
            ),
            "project_id": (
                tenant.project_id
            ),
            "environment_id": (
                tenant.environment_id
            ),
            "producer": event.producer,
            "metric": event.metric,
            "unit": event.unit,
            "quantity": quantity,
            "occurred_at": (
                event.occurred_at
            ),
            "dimensions": (
                event.dimensions
            ),
            "source_ref": (
                event.source_ref
            ),
        }

        event_hash = sha256(
            _canonical_json(
                canonical_event
            ).encode("utf-8")
        ).hexdigest()

        idem_key = (
            tenant.organization_id,
            tenant.environment_id,
            event.producer,
            event.idempotency_key,
        )

        existing = self._idempotency.get(
            idem_key
        )

        if existing is not None:
            existing_hash, usage_id = (
                existing
            )

            if existing_hash != event_hash:
                raise MeteringBaaSError(
                    "idempotency key reused with different usage event"
                )

            return {
                "created": False,
                "record": self._records[
                    usage_id
                ],
                "audit_event": None,
            }

        usage_id = (
            "usage_"
            + sha256(
                _canonical_json(
                    {
                        "idempotency_scope": (
                            idem_key
                        ),
                        "event_hash": (
                            event_hash
                        ),
                    }
                ).encode("utf-8")
            ).hexdigest()[:24]
        )

        body = {
            "usage_id": usage_id,
            **canonical_event,
            "correlation_id": (
                request_context.correlation_id
            ),
            "actor_id": (
                request_context.actor_id
            ),
            "kernel_authorization_ref": (
                request_context.kernel_authorization_ref
            ),
        }

        record_hash = sha256(
            _canonical_json(
                body
            ).encode("utf-8")
        ).hexdigest()

        record = UsageRecord(
            usage_id=usage_id,
            tenant=tenant,
            producer=event.producer,
            idempotency_key=(
                event.idempotency_key
            ),
            metric=event.metric,
            unit=event.unit,
            quantity=quantity,
            occurred_at=(
                event.occurred_at
            ),
            dimensions=dict(
                event.dimensions
            ),
            source_ref=(
                event.source_ref
            ),
            correlation_id=(
                request_context.correlation_id
            ),
            actor_id=(
                request_context.actor_id
            ),
            kernel_authorization_ref=(
                request_context.kernel_authorization_ref
            ),
            record_hash=record_hash,
            ingested_at=_time(
                ingested_at
            ).isoformat(),
        )
        record.validate()

        self._records[
            usage_id
        ] = record
        self._idempotency[
            idem_key
        ] = (
            event_hash,
            usage_id,
        )

        audit_event = {
            "audit_id": (
                "audit_usage_"
                + usage_id.removeprefix(
                    "usage_"
                )
            ),
            "organization_id": (
                tenant.organization_id
            ),
            "actor_type": (
                request_context.actor_type
            ),
            "actor_id": (
                request_context.actor_id
            ),
            "action": (
                "usage_metering.ingest"
            ),
            "resource_type": (
                "usage_record"
            ),
            "resource_id": (
                usage_id
            ),
            "timestamp": (
                record.ingested_at
            ),
            "correlation_id": (
                request_context.correlation_id
            ),
            "metadata": {
                "metric": (
                    record.metric
                ),
                "unit": (
                    record.unit
                ),
                "quantity": (
                    record.quantity
                ),
                "producer": (
                    record.producer
                ),
                "record_hash": (
                    record.record_hash
                ),
            },
        }

        return {
            "created": True,
            "record": record,
            "audit_event": audit_event,
        }

    def get(
        self,
        *,
        usage_id: str,
        request_context: Any,
    ) -> UsageRecord:
        self._validate_request_context(
            request_context
        )

        record = self._records.get(
            str(
                usage_id
            ).strip()
        )

        if record is None:
            raise MeteringBaaSError(
                "usage record not found"
            )

        tenant = self._tenant_from_context(
            request_context
        )

        if not self._tenant_equal(
            record.tenant,
            tenant,
        ):
            raise MeteringBaaSError(
                "cross-tenant usage access denied"
            )

        return record

    def aggregate(
        self,
        *,
        metric: str,
        unit: str,
        period_start: str,
        period_end: str,
        request_context: Any,
        generated_at: str | None = None,
    ) -> UsageAggregate:
        self._validate_request_context(
            request_context
        )

        metric = str(
            metric
        ).strip()

        if metric not in METRICS:
            raise MeteringBaaSError(
                f"unsupported metric: {metric}"
            )

        unit = str(
            unit
        ).strip()

        if not UNIT_PATTERN.fullmatch(
            unit
        ):
            raise MeteringBaaSError(
                "invalid aggregate unit"
            )

        start = _time(
            period_start
        )
        end = _time(
            period_end
        )

        if start >= end:
            raise MeteringBaaSError(
                "period_start must be before period_end"
            )

        tenant = self._tenant_from_context(
            request_context
        )

        selected = [
            record
            for record in self._records.values()
            if self._tenant_equal(
                record.tenant,
                tenant,
            )
            and record.metric == metric
            and record.unit == unit
            and start
            <= _time(
                record.occurred_at
            )
            < end
        ]

        selected.sort(
            key=lambda record: (
                record.occurred_at,
                record.usage_id,
            )
        )

        total = sum(
            (
                Decimal(
                    record.quantity
                )
                for record in selected
            ),
            Decimal("0"),
        )

        total_quantity = (
            canonical_quantity(
                format(
                    total,
                    "f",
                )
            )
        )

        source_hash = sha256(
            _canonical_json(
                [
                    record.record_hash
                    for record in selected
                ]
            ).encode("utf-8")
        ).hexdigest()

        criteria = {
            "organization_id": (
                tenant.organization_id
            ),
            "workspace_id": (
                tenant.workspace_id
            ),
            "project_id": (
                tenant.project_id
            ),
            "environment_id": (
                tenant.environment_id
            ),
            "metric": metric,
            "unit": unit,
            "period_start": (
                start.isoformat()
            ),
            "period_end": (
                end.isoformat()
            ),
            "source_hash": (
                source_hash
            ),
        }

        aggregate_id = (
            "usage_agg_"
            + sha256(
                _canonical_json(
                    criteria
                ).encode("utf-8")
            ).hexdigest()[:24]
        )

        generated = _time(
            generated_at
        ).isoformat()

        audit_event = {
            "audit_id": (
                "audit_"
                + aggregate_id
            ),
            "organization_id": (
                tenant.organization_id
            ),
            "actor_type": (
                request_context.actor_type
            ),
            "actor_id": (
                request_context.actor_id
            ),
            "action": (
                "usage_metering.aggregate"
            ),
            "resource_type": (
                "usage_aggregate"
            ),
            "resource_id": (
                aggregate_id
            ),
            "timestamp": generated,
            "correlation_id": (
                request_context.correlation_id
            ),
            "metadata": {
                "metric": metric,
                "unit": unit,
                "event_count": (
                    len(selected)
                ),
                "total_quantity": (
                    total_quantity
                ),
                "source_hash": (
                    source_hash
                ),
            },
        }

        return UsageAggregate(
            aggregate_id=aggregate_id,
            tenant=tenant,
            metric=metric,
            unit=unit,
            total_quantity=(
                total_quantity
            ),
            event_count=len(
                selected
            ),
            period_start=(
                start.isoformat()
            ),
            period_end=(
                end.isoformat()
            ),
            source_hash=source_hash,
            source_usage_ids=tuple(
                record.usage_id
                for record in selected
            ),
            generated_at=generated,
            audit_event=audit_event,
        )

    def reconcile(
        self,
        *,
        aggregate: UsageAggregate,
        request_context: Any,
    ) -> dict[str, Any]:
        self._validate_request_context(
            request_context
        )

        tenant = self._tenant_from_context(
            request_context
        )

        if not self._tenant_equal(
            aggregate.tenant,
            tenant,
        ):
            raise MeteringBaaSError(
                "cross-tenant aggregate reconciliation denied"
            )

        recomputed = self.aggregate(
            metric=aggregate.metric,
            unit=aggregate.unit,
            period_start=(
                aggregate.period_start
            ),
            period_end=(
                aggregate.period_end
            ),
            request_context=(
                request_context
            ),
            generated_at=(
                aggregate.generated_at
            ),
        )

        checks = {
            "total_quantity": (
                recomputed.total_quantity
                == aggregate.total_quantity
            ),
            "event_count": (
                recomputed.event_count
                == aggregate.event_count
            ),
            "source_hash": (
                recomputed.source_hash
                == aggregate.source_hash
            ),
            "source_usage_ids": (
                recomputed.source_usage_ids
                == aggregate.source_usage_ids
            ),
        }

        return {
            "valid": all(
                checks.values()
            ),
            "checks": checks,
            "aggregate_id": (
                aggregate.aggregate_id
            ),
        }

    def list_records(
        self,
        *,
        request_context: Any,
    ) -> tuple[
        UsageRecord,
        ...
    ]:
        self._validate_request_context(
            request_context
        )

        tenant = self._tenant_from_context(
            request_context
        )

        records = [
            record
            for record in self._records.values()
            if self._tenant_equal(
                record.tenant,
                tenant,
            )
        ]

        records.sort(
            key=lambda record: (
                record.occurred_at,
                record.usage_id,
            )
        )

        return tuple(
            records
        )
