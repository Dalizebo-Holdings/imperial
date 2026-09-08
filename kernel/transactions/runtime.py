from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


TRANSACTION_STATES = {
    "NEW",
    "ACTIVE",
    "COMMITTED",
    "ROLLED_BACK",
}


class TransactionError(ValueError):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class InMemoryTransactionBackend:
    resources: dict[str, dict[str, Any]] = field(
        default_factory=dict
    )
    audit_records: list[dict[str, Any]] = field(
        default_factory=list
    )
    outbox: list[dict[str, Any]] = field(
        default_factory=list
    )

    def snapshot(self) -> dict[str, Any]:
        return {
            "resources": deepcopy(self.resources),
            "audit_records": deepcopy(self.audit_records),
            "outbox": deepcopy(self.outbox),
        }


@dataclass
class Transaction:
    transaction_id: str
    backend: InMemoryTransactionBackend
    correlation_id: str
    state: str = "NEW"
    started_at: str | None = None
    committed_at: str | None = None
    rolled_back_at: str | None = None
    _mutations: list[tuple[str, dict[str, Any]]] = field(
        default_factory=list
    )
    _audit: list[dict[str, Any]] = field(
        default_factory=list
    )
    _outbox: list[dict[str, Any]] = field(
        default_factory=list
    )

    def _require_state(self, expected: str) -> None:
        if self.state != expected:
            raise TransactionError(
                f"transaction state must be {expected}, found {self.state}"
            )

    def begin(self, *, now: str | None = None) -> None:
        self._require_state("NEW")

        if not str(self.transaction_id).strip():
            raise TransactionError(
                "transaction_id must not be empty"
            )

        if not str(self.correlation_id).strip():
            raise TransactionError(
                "correlation_id must not be empty"
            )

        self.state = "ACTIVE"
        self.started_at = now or _now_iso()

    def stage_resource(
        self,
        *,
        resource_key: str,
        value: dict[str, Any],
    ) -> None:
        self._require_state("ACTIVE")

        if not str(resource_key).strip():
            raise TransactionError(
                "resource_key must not be empty"
            )

        if not isinstance(value, dict):
            raise TransactionError(
                "resource value must be an object"
            )

        self._mutations.append(
            (str(resource_key).strip(), deepcopy(value))
        )

    def stage_audit(
        self,
        record: dict[str, Any],
    ) -> None:
        self._require_state("ACTIVE")

        if not isinstance(record, dict):
            raise TransactionError(
                "audit record must be an object"
            )

        material = deepcopy(record)
        material.setdefault(
            "correlation_id",
            self.correlation_id,
        )
        self._audit.append(material)

    def stage_outbox(
        self,
        event: dict[str, Any],
    ) -> None:
        self._require_state("ACTIVE")

        if not isinstance(event, dict):
            raise TransactionError(
                "outbox event must be an object"
            )

        required = {
            "event_id",
            "event_type",
            "organization_id",
            "resource_type",
            "resource_id",
            "correlation_id",
            "actor_type",
            "actor_id",
            "payload",
        }

        missing = [
            field_name
            for field_name in sorted(required)
            if field_name not in event
        ]

        if missing:
            raise TransactionError(
                "outbox event missing fields: "
                + ", ".join(missing)
            )

        self._outbox.append(deepcopy(event))

    def pending_counts(self) -> dict[str, int]:
        return {
            "mutations": len(self._mutations),
            "audit_records": len(self._audit),
            "outbox_events": len(self._outbox),
        }

    def commit(
        self,
        *,
        now: str | None = None,
    ) -> dict[str, int]:
        self._require_state("ACTIVE")

        next_resources = deepcopy(self.backend.resources)
        next_audit = deepcopy(self.backend.audit_records)
        next_outbox = deepcopy(self.backend.outbox)

        for resource_key, value in self._mutations:
            next_resources[resource_key] = deepcopy(value)

        next_audit.extend(deepcopy(self._audit))

        for event in self._outbox:
            committed_event = deepcopy(event)
            committed_event["outbox_status"] = "COMMITTED"
            next_outbox.append(committed_event)

        # Atomic visibility point for the reference backend.
        self.backend.resources = next_resources
        self.backend.audit_records = next_audit
        self.backend.outbox = next_outbox

        self.state = "COMMITTED"
        self.committed_at = now or _now_iso()

        return self.pending_counts()

    def rollback(
        self,
        *,
        now: str | None = None,
    ) -> None:
        self._require_state("ACTIVE")
        self._mutations.clear()
        self._audit.clear()
        self._outbox.clear()
        self.state = "ROLLED_BACK"
        self.rolled_back_at = now or _now_iso()

    @property
    def publishable_outbox(self) -> list[dict[str, Any]]:
        if self.state != "COMMITTED":
            return []

        return [
            deepcopy(event)
            for event in self.backend.outbox
            if event.get("outbox_status") == "COMMITTED"
        ]
