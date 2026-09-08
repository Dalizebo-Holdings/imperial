from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Any


STATUSES = {
    "IN_PROGRESS",
    "COMPLETED",
    "FAILED",
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
}


class IdempotencyError(ValueError):
    pass


class IdempotencyConflict(IdempotencyError):
    pass


def _contains_sensitive_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).strip().lower() in SENSITIVE_KEYS:
                return True
            if _contains_sensitive_key(item):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def canonical_request_hash(payload: Any) -> str:
    if _contains_sensitive_key(payload):
        raise IdempotencyError(
            "request payload contains a sensitive field"
        )

    try:
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise IdempotencyError(
            "request payload must be JSON-compatible"
        ) from exc

    return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class IdempotencyRecord:
    key: str
    organization_id: str
    operation: str
    request_hash: str
    status: str
    response_reference: str | None
    created_at: str
    expires_at: str

    def validate(self) -> None:
        required = {
            "key": self.key,
            "organization_id": self.organization_id,
            "operation": self.operation,
            "request_hash": self.request_hash,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }

        missing = [
            name
            for name, value in required.items()
            if not str(value).strip()
        ]

        if missing:
            raise IdempotencyError(
                "missing idempotency fields: "
                + ", ".join(missing)
            )

        if self.status not in STATUSES:
            raise IdempotencyError(
                f"invalid idempotency status: {self.status}"
            )

        if len(self.request_hash) != 64:
            raise IdempotencyError(
                "request_hash must be SHA-256 hex"
            )

        datetime.fromisoformat(self.created_at)
        datetime.fromisoformat(self.expires_at)


class IdempotencyStore:
    def __init__(self) -> None:
        self._records: dict[
            tuple[str, str, str],
            IdempotencyRecord,
        ] = {}

    @staticmethod
    def _identity(
        *,
        organization_id: str,
        operation: str,
        key: str,
    ) -> tuple[str, str, str]:
        values = [
            str(organization_id).strip(),
            str(operation).strip(),
            str(key).strip(),
        ]

        if not all(values):
            raise IdempotencyError(
                "organization_id, operation and key are required"
            )

        return tuple(values)

    def begin(
        self,
        *,
        organization_id: str,
        operation: str,
        key: str,
        payload: Any,
        now: str | None = None,
        ttl_seconds: int = 86400,
    ) -> tuple[IdempotencyRecord, bool]:
        if not isinstance(ttl_seconds, int) or ttl_seconds < 1:
            raise IdempotencyError(
                "ttl_seconds must be a positive integer"
            )

        identity = self._identity(
            organization_id=organization_id,
            operation=operation,
            key=key,
        )

        request_hash = canonical_request_hash(payload)

        current = (
            datetime.fromisoformat(now)
            if now is not None
            else datetime.now(timezone.utc)
        )

        existing = self._records.get(identity)

        if existing is not None:
            expires = datetime.fromisoformat(
                existing.expires_at
            )

            if current < expires:
                if existing.request_hash != request_hash:
                    raise IdempotencyConflict(
                        "same idempotency key reused with different request hash"
                    )

                return replace(existing), False

        record = IdempotencyRecord(
            key=identity[2],
            organization_id=identity[0],
            operation=identity[1],
            request_hash=request_hash,
            status="IN_PROGRESS",
            response_reference=None,
            created_at=current.isoformat(),
            expires_at=(
                current + timedelta(seconds=ttl_seconds)
            ).isoformat(),
        )
        record.validate()
        self._records[identity] = record

        return replace(record), True

    def complete(
        self,
        *,
        organization_id: str,
        operation: str,
        key: str,
        response_reference: str,
    ) -> IdempotencyRecord:
        return self._set_terminal(
            organization_id=organization_id,
            operation=operation,
            key=key,
            status="COMPLETED",
            response_reference=response_reference,
        )

    def fail(
        self,
        *,
        organization_id: str,
        operation: str,
        key: str,
        response_reference: str | None = None,
    ) -> IdempotencyRecord:
        return self._set_terminal(
            organization_id=organization_id,
            operation=operation,
            key=key,
            status="FAILED",
            response_reference=response_reference,
        )

    def _set_terminal(
        self,
        *,
        organization_id: str,
        operation: str,
        key: str,
        status: str,
        response_reference: str | None,
    ) -> IdempotencyRecord:
        identity = self._identity(
            organization_id=organization_id,
            operation=operation,
            key=key,
        )

        current = self._records.get(identity)

        if current is None:
            raise IdempotencyError(
                "idempotency record not found"
            )

        if current.status != "IN_PROGRESS":
            raise IdempotencyError(
                f"idempotency record already terminal: {current.status}"
            )

        if status == "COMPLETED" and not str(
            response_reference or ""
        ).strip():
            raise IdempotencyError(
                "completed idempotency record requires response_reference"
            )

        updated = IdempotencyRecord(
            key=current.key,
            organization_id=current.organization_id,
            operation=current.operation,
            request_hash=current.request_hash,
            status=status,
            response_reference=response_reference,
            created_at=current.created_at,
            expires_at=current.expires_at,
        )
        updated.validate()
        self._records[identity] = updated
        return replace(updated)

    def get(
        self,
        *,
        organization_id: str,
        operation: str,
        key: str,
    ) -> IdempotencyRecord | None:
        identity = self._identity(
            organization_id=organization_id,
            operation=operation,
            key=key,
        )

        record = self._records.get(identity)
        return replace(record) if record else None
