from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Callable


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


class AuditBaaSError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    result = str(value).strip()
    if not result:
        raise AuditBaaSError(
            f"{name} must not be empty"
        )
    return result


def _time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise AuditBaaSError(
            "timestamp must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise AuditBaaSError(
            "timestamp must be timezone-aware"
        )

    return parsed


def _canonical(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except (TypeError, ValueError) as exc:
        raise AuditBaaSError(
            "value must be JSON-compatible"
        ) from exc


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if (
                str(key).strip().lower()
                in SENSITIVE_KEYS
            ):
                result[key] = "[REDACTED]"
            else:
                result[key] = _sanitize(
                    item
                )
        return result

    if isinstance(value, list):
        return [
            _sanitize(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            _sanitize(item)
            for item in value
        ]

    return value


@dataclass(frozen=True)
class AuditQuery:
    actor_id: str | None = None
    action: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    correlation_id: str | None = None
    timestamp_from: str | None = None
    timestamp_to: str | None = None
    after_sequence: int = 0
    limit: int = 100

    def validate(self) -> None:
        if (
            not isinstance(
                self.after_sequence,
                int,
            )
            or self.after_sequence < 0
        ):
            raise AuditBaaSError(
                "after_sequence must be an integer >= 0"
            )

        if (
            not isinstance(
                self.limit,
                int,
            )
            or self.limit < 1
            or self.limit > 1000
        ):
            raise AuditBaaSError(
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
            raise AuditBaaSError(
                "timestamp_from may not exceed timestamp_to"
            )


@dataclass(frozen=True)
class AuditQueryResult:
    organization_id: str
    source_count: int
    source_last_hash: str
    records: tuple[dict[str, Any], ...]
    next_after_sequence: int | None
    access_audit_event: dict[str, Any]
    log_context: dict[str, Any]


@dataclass(frozen=True)
class AuditExport:
    export_id: str
    organization_id: str
    generated_at: str
    source_count: int
    source_last_hash: str
    selected_count: int
    selection_hash: str
    criteria: dict[str, Any]
    projected_records: tuple[
        dict[str, Any],
        ...
    ]
    access_audit_event: dict[str, Any]

    def verify_selection(self) -> bool:
        supplied = sha256(
            _canonical(
                list(
                    self.projected_records
                )
            ).encode("utf-8")
        ).hexdigest()

        return supplied == (
            self.selection_hash
        )


class AuditService:
    def __init__(
        self,
        *,
        kernel_verify_records: Callable[
            [list[dict[str, Any]]],
            dict[str, Any],
        ],
    ) -> None:
        if not callable(
            kernel_verify_records
        ):
            raise AuditBaaSError(
                "kernel_verify_records must be callable"
            )

        self._verify = (
            kernel_verify_records
        )

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
            "service",
            "operation",
            "request_id",
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
            != "audit"
        ):
            raise AuditBaaSError(
                "AuditService requires service=audit"
            )

        if not str(
            request_context.kernel_authorization_ref
        ).startswith(
            "kernel_auth_"
        ):
            raise AuditBaaSError(
                "audit access requires Kernel authorization evidence"
            )

    def _verified_source(
        self,
        records: list[
            dict[str, Any]
        ],
    ) -> dict[str, Any]:
        if not isinstance(
            records,
            list,
        ):
            raise AuditBaaSError(
                "records must be a list"
            )

        verification = self._verify(
            records
        )

        if (
            not isinstance(
                verification,
                dict,
            )
            or not verification.get(
                "valid"
            )
        ):
            reason = (
                verification.get(
                    "reason",
                    "unknown",
                )
                if isinstance(
                    verification,
                    dict,
                )
                else "invalid_result"
            )

            raise AuditBaaSError(
                "Kernel audit verification failed: "
                + str(reason)
            )

        return verification

    @staticmethod
    def _validate_record(
        record: dict[str, Any],
    ) -> None:
        required = {
            "audit_version",
            "sequence",
            "event",
            "previous_hash",
            "record_hash",
        }

        if not isinstance(
            record,
            dict,
        ):
            raise AuditBaaSError(
                "audit record must be an object"
            )

        if not required.issubset(
            record
        ):
            raise AuditBaaSError(
                "audit record is missing required fields"
            )

        event = record.get(
            "event"
        )

        if not isinstance(
            event,
            dict,
        ):
            raise AuditBaaSError(
                "audit record event must be an object"
            )

        required_event = {
            "audit_id",
            "organization_id",
            "actor_type",
            "actor_id",
            "action",
            "resource_type",
            "resource_id",
            "timestamp",
            "correlation_id",
            "metadata",
        }

        if not required_event.issubset(
            event
        ):
            raise AuditBaaSError(
                "audit event is missing required fields"
            )

        if (
            not isinstance(
                record["sequence"],
                int,
            )
            or record["sequence"] < 1
        ):
            raise AuditBaaSError(
                "audit sequence must be >= 1"
            )

        _time(
            str(
                event["timestamp"]
            )
        )

    @staticmethod
    def _matches(
        record: dict[str, Any],
        *,
        organization_id: str,
        query: AuditQuery,
    ) -> bool:
        event = record[
            "event"
        ]

        if (
            str(
                event[
                    "organization_id"
                ]
            )
            != organization_id
        ):
            return False

        if (
            record["sequence"]
            <= query.after_sequence
        ):
            return False

        for field_name in [
            "actor_id",
            "action",
            "resource_type",
            "resource_id",
            "correlation_id",
        ]:
            expected = getattr(
                query,
                field_name,
            )

            if (
                expected is not None
                and str(
                    event[
                        field_name
                    ]
                )
                != str(expected)
            ):
                return False

        timestamp = _time(
            str(
                event[
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
            return False

        if (
            query.timestamp_to
            and timestamp
            > _time(
                query.timestamp_to
            )
        ):
            return False

        return True

    @staticmethod
    def _project(
        record: dict[str, Any],
    ) -> dict[str, Any]:
        event = record[
            "event"
        ]

        return {
            "sequence": (
                record[
                    "sequence"
                ]
            ),
            "record_hash": (
                str(
                    record[
                        "record_hash"
                    ]
                )
            ),
            "audit_id": (
                str(
                    event[
                        "audit_id"
                    ]
                )
            ),
            "actor_type": (
                str(
                    event[
                        "actor_type"
                    ]
                )
            ),
            "actor_id": (
                str(
                    event[
                        "actor_id"
                    ]
                )
            ),
            "action": (
                str(
                    event[
                        "action"
                    ]
                )
            ),
            "resource_type": (
                str(
                    event[
                        "resource_type"
                    ]
                )
            ),
            "resource_id": (
                str(
                    event[
                        "resource_id"
                    ]
                )
            ),
            "timestamp": (
                str(
                    event[
                        "timestamp"
                    ]
                )
            ),
            "correlation_id": (
                str(
                    event[
                        "correlation_id"
                    ]
                )
            ),
            "metadata": _sanitize(
                event.get(
                    "metadata",
                    {},
                )
            ),
        }

    @staticmethod
    def _access_event(
        *,
        request_context: Any,
        action: str,
        selected_count: int,
        source_count: int,
        criteria_hash: str,
    ) -> dict[str, Any]:
        material = {
            "request_id": (
                request_context.request_id
            ),
            "organization_id": (
                request_context.organization_id
            ),
            "actor_id": (
                request_context.actor_id
            ),
            "action": action,
            "criteria_hash": (
                criteria_hash
            ),
        }

        audit_id = (
            "audit_access_"
            + sha256(
                _canonical(
                    material
                ).encode("utf-8")
            ).hexdigest()[:24]
        )

        return {
            "audit_id": audit_id,
            "organization_id": (
                request_context.organization_id
            ),
            "actor_type": (
                request_context.actor_type
            ),
            "actor_id": (
                request_context.actor_id
            ),
            "action": action,
            "resource_type": (
                "audit_evidence"
            ),
            "resource_id": (
                request_context.request_id
            ),
            "timestamp": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
            "correlation_id": (
                request_context.correlation_id
            ),
            "metadata": {
                "selected_count": (
                    selected_count
                ),
                "source_count": (
                    source_count
                ),
                "criteria_hash": (
                    criteria_hash
                ),
                "kernel_authorization_ref": (
                    request_context.kernel_authorization_ref
                ),
            },
        }

    def query(
        self,
        *,
        records: list[
            dict[str, Any]
        ],
        query: AuditQuery,
        request_context: Any,
    ) -> AuditQueryResult:
        self._validate_request_context(
            request_context
        )
        query.validate()

        verification = (
            self._verified_source(
                records
            )
        )

        for record in records:
            self._validate_record(
                record
            )

        selected = [
            record
            for record in records
            if self._matches(
                record,
                organization_id=(
                    request_context.organization_id
                ),
                query=query,
            )
        ]

        selected.sort(
            key=lambda item: (
                item["sequence"]
            )
        )

        page = selected[
            : query.limit
        ]

        projected = tuple(
            self._project(
                record
            )
            for record in page
        )

        more = (
            len(selected)
            > len(page)
        )

        next_sequence = (
            page[-1][
                "sequence"
            ]
            if more and page
            else None
        )

        criteria = {
            "actor_id": query.actor_id,
            "action": query.action,
            "resource_type": (
                query.resource_type
            ),
            "resource_id": (
                query.resource_id
            ),
            "correlation_id": (
                query.correlation_id
            ),
            "timestamp_from": (
                query.timestamp_from
            ),
            "timestamp_to": (
                query.timestamp_to
            ),
            "after_sequence": (
                query.after_sequence
            ),
            "limit": query.limit,
        }

        criteria_hash = sha256(
            _canonical(
                criteria
            ).encode("utf-8")
        ).hexdigest()

        access_event = (
            self._access_event(
                request_context=(
                    request_context
                ),
                action="audit.query",
                selected_count=(
                    len(projected)
                ),
                source_count=(
                    int(
                        verification.get(
                            "count",
                            len(records),
                        )
                    )
                ),
                criteria_hash=(
                    criteria_hash
                ),
            )
        )

        return AuditQueryResult(
            organization_id=(
                request_context.organization_id
            ),
            source_count=int(
                verification.get(
                    "count",
                    len(records),
                )
            ),
            source_last_hash=str(
                verification.get(
                    "last_hash",
                    "",
                )
            ),
            records=projected,
            next_after_sequence=(
                next_sequence
            ),
            access_audit_event=(
                access_event
            ),
            log_context={
                "service": "audit",
                "operation": (
                    "audit.query"
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
                    len(projected)
                ),
            },
        )

    def export(
        self,
        *,
        records: list[
            dict[str, Any]
        ],
        query: AuditQuery,
        request_context: Any,
        generated_at: str | None = None,
    ) -> AuditExport:
        result = self.query(
            records=records,
            query=query,
            request_context=request_context,
        )

        generated = (
            _time(
                generated_at
            ).isoformat()
            if generated_at
            else datetime.now(
                timezone.utc
            ).isoformat()
        )

        criteria = {
            "actor_id": query.actor_id,
            "action": query.action,
            "resource_type": (
                query.resource_type
            ),
            "resource_id": (
                query.resource_id
            ),
            "correlation_id": (
                query.correlation_id
            ),
            "timestamp_from": (
                query.timestamp_from
            ),
            "timestamp_to": (
                query.timestamp_to
            ),
            "after_sequence": (
                query.after_sequence
            ),
            "limit": query.limit,
        }

        selection_hash = sha256(
            _canonical(
                list(
                    result.records
                )
            ).encode("utf-8")
        ).hexdigest()

        export_material = {
            "organization_id": (
                result.organization_id
            ),
            "generated_at": (
                generated
            ),
            "source_last_hash": (
                result.source_last_hash
            ),
            "selection_hash": (
                selection_hash
            ),
            "criteria": criteria,
        }

        export_id = (
            "audit_export_"
            + sha256(
                _canonical(
                    export_material
                ).encode("utf-8")
            ).hexdigest()[:24]
        )

        criteria_hash = sha256(
            _canonical(
                criteria
            ).encode("utf-8")
        ).hexdigest()

        access_event = (
            self._access_event(
                request_context=(
                    request_context
                ),
                action="audit.export",
                selected_count=(
                    len(
                        result.records
                    )
                ),
                source_count=(
                    result.source_count
                ),
                criteria_hash=(
                    criteria_hash
                ),
            )
        )

        return AuditExport(
            export_id=export_id,
            organization_id=(
                result.organization_id
            ),
            generated_at=generated,
            source_count=(
                result.source_count
            ),
            source_last_hash=(
                result.source_last_hash
            ),
            selected_count=len(
                result.records
            ),
            selection_hash=(
                selection_hash
            ),
            criteria=criteria,
            projected_records=(
                result.records
            ),
            access_audit_event=(
                access_event
            ),
        )
