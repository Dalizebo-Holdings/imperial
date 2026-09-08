from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
import secrets
from typing import Any


ACTOR_TYPES = {
    "HUMAN_USER",
    "SERVICE_ACCOUNT",
    "API_CLIENT",
}

SESSION_STATUSES = {
    "ACTIVE",
    "REVOKED",
    "EXPIRED",
}


class AuthenticationError(ValueError):
    pass


def _now(value: str | None = None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)

    parsed = datetime.fromisoformat(value)

    if parsed.tzinfo is None:
        raise AuthenticationError(
            "timestamps must be timezone-aware ISO-8601"
        )

    return parsed


def _fingerprint(value: str) -> str:
    material = str(value)

    if not material:
        raise AuthenticationError(
            "credential material must not be empty"
        )

    return sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class IdentityRecord:
    actor_id: str
    actor_type: str
    organization_id: str
    identity_ref: str
    enabled: bool = True
    metadata: dict[str, Any] | None = None

    def validate(self) -> None:
        required = {
            "actor_id": self.actor_id,
            "organization_id": self.organization_id,
            "identity_ref": self.identity_ref,
        }

        missing = [
            name
            for name, value in required.items()
            if not str(value).strip()
        ]

        if missing:
            raise AuthenticationError(
                "missing identity fields: "
                + ", ".join(missing)
            )

        if self.actor_type not in ACTOR_TYPES:
            raise AuthenticationError(
                f"unsupported actor_type: {self.actor_type}"
            )


@dataclass(frozen=True)
class SessionRecord:
    session_id: str
    actor_id: str
    organization_id: str
    token_fingerprint: str
    status: str
    authentication_method: str
    created_at: str
    expires_at: str
    revoked_at: str | None = None
    mfa_verified: bool = False

    def validate(self) -> None:
        for name, value in {
            "session_id": self.session_id,
            "actor_id": self.actor_id,
            "organization_id": self.organization_id,
            "token_fingerprint": self.token_fingerprint,
            "authentication_method": self.authentication_method,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }.items():
            if not str(value).strip():
                raise AuthenticationError(
                    f"{name} must not be empty"
                )

        if self.status not in SESSION_STATUSES:
            raise AuthenticationError(
                f"invalid session status: {self.status}"
            )

        if len(self.token_fingerprint) != 64:
            raise AuthenticationError(
                "token_fingerprint must be SHA-256 hex"
            )

        _now(self.created_at)
        _now(self.expires_at)

        if self.revoked_at is not None:
            _now(self.revoked_at)


@dataclass(frozen=True)
class APIKeyRecord:
    key_id: str
    actor_id: str
    organization_id: str
    key_fingerprint: str
    created_at: str
    expires_at: str | None
    enabled: bool
    scopes: tuple[str, ...]

    def validate(self) -> None:
        for name, value in {
            "key_id": self.key_id,
            "actor_id": self.actor_id,
            "organization_id": self.organization_id,
            "key_fingerprint": self.key_fingerprint,
            "created_at": self.created_at,
        }.items():
            if not str(value).strip():
                raise AuthenticationError(
                    f"{name} must not be empty"
                )

        if len(self.key_fingerprint) != 64:
            raise AuthenticationError(
                "key_fingerprint must be SHA-256 hex"
            )

        _now(self.created_at)

        if self.expires_at is not None:
            _now(self.expires_at)


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    actor_id: str
    actor_type: str
    organization_id: str
    authenticated: bool
    authentication_method: str
    identity_ref: str
    session_ref: str | None
    mfa_verified: bool


class AuthenticationRegistry:
    def __init__(self) -> None:
        self._identities: dict[str, IdentityRecord] = {}
        self._sessions: dict[str, SessionRecord] = {}
        self._api_keys: dict[str, APIKeyRecord] = {}

    def register_identity(
        self,
        identity: IdentityRecord,
    ) -> None:
        identity.validate()

        if identity.actor_id in self._identities:
            raise AuthenticationError(
                f"identity already registered: {identity.actor_id}"
            )

        self._identities[identity.actor_id] = identity

    def get_identity(self, actor_id: str) -> IdentityRecord:
        identity = self._identities.get(str(actor_id).strip())

        if identity is None:
            raise AuthenticationError(
                f"unknown identity: {actor_id}"
            )

        return identity

    def issue_session(
        self,
        *,
        actor_id: str,
        organization_id: str,
        authentication_method: str,
        ttl_seconds: int = 3600,
        mfa_verified: bool = False,
        now: str | None = None,
    ) -> tuple[SessionRecord, str]:
        identity = self.get_identity(actor_id)

        if not identity.enabled:
            raise AuthenticationError(
                "identity is disabled"
            )

        if identity.organization_id != organization_id:
            raise AuthenticationError(
                "identity organization mismatch"
            )

        if not isinstance(ttl_seconds, int) or ttl_seconds < 1:
            raise AuthenticationError(
                "ttl_seconds must be an integer >= 1"
            )

        current = _now(now)
        raw_token = secrets.token_urlsafe(48)
        session_id = "sess_" + secrets.token_hex(16)

        record = SessionRecord(
            session_id=session_id,
            actor_id=identity.actor_id,
            organization_id=organization_id,
            token_fingerprint=_fingerprint(raw_token),
            status="ACTIVE",
            authentication_method=str(
                authentication_method
            ).strip(),
            created_at=current.isoformat(),
            expires_at=(
                current + timedelta(seconds=ttl_seconds)
            ).isoformat(),
            mfa_verified=bool(mfa_verified),
        )
        record.validate()
        self._sessions[record.session_id] = record

        return record, raw_token

    def authenticate_session(
        self,
        *,
        session_id: str,
        raw_token: str,
        organization_id: str,
        now: str | None = None,
    ) -> AuthenticatedPrincipal:
        record = self._sessions.get(session_id)

        if record is None:
            raise AuthenticationError(
                "session not found"
            )

        record.validate()

        if record.status != "ACTIVE":
            raise AuthenticationError(
                "session is not active"
            )

        if record.organization_id != organization_id:
            raise AuthenticationError(
                "session organization mismatch"
            )

        current = _now(now)

        if current >= _now(record.expires_at):
            self._sessions[session_id] = replace(
                record,
                status="EXPIRED",
            )
            raise AuthenticationError(
                "session has expired"
            )

        supplied = _fingerprint(raw_token)

        if not hmac.compare_digest(
            supplied,
            record.token_fingerprint,
        ):
            raise AuthenticationError(
                "session credential mismatch"
            )

        identity = self.get_identity(record.actor_id)

        if not identity.enabled:
            raise AuthenticationError(
                "identity is disabled"
            )

        return AuthenticatedPrincipal(
            actor_id=identity.actor_id,
            actor_type=identity.actor_type,
            organization_id=identity.organization_id,
            authenticated=True,
            authentication_method=(
                record.authentication_method
            ),
            identity_ref=identity.identity_ref,
            session_ref=record.session_id,
            mfa_verified=record.mfa_verified,
        )

    def revoke_session(
        self,
        session_id: str,
        *,
        now: str | None = None,
    ) -> SessionRecord:
        record = self._sessions.get(session_id)

        if record is None:
            raise AuthenticationError(
                "session not found"
            )

        if record.status != "ACTIVE":
            raise AuthenticationError(
                f"session already terminal: {record.status}"
            )

        updated = replace(
            record,
            status="REVOKED",
            revoked_at=_now(now).isoformat(),
        )
        self._sessions[session_id] = updated
        return updated

    def issue_api_key(
        self,
        *,
        actor_id: str,
        organization_id: str,
        scopes: list[str],
        ttl_seconds: int | None = None,
        now: str | None = None,
    ) -> tuple[APIKeyRecord, str]:
        identity = self.get_identity(actor_id)

        if not identity.enabled:
            raise AuthenticationError(
                "identity is disabled"
            )

        if identity.organization_id != organization_id:
            raise AuthenticationError(
                "identity organization mismatch"
            )

        normalized_scopes = tuple(
            sorted({
                str(scope).strip()
                for scope in scopes
                if str(scope).strip()
            })
        )

        if not normalized_scopes:
            raise AuthenticationError(
                "API key scopes must not be empty"
            )

        current = _now(now)
        expires_at = None

        if ttl_seconds is not None:
            if (
                not isinstance(ttl_seconds, int)
                or ttl_seconds < 1
            ):
                raise AuthenticationError(
                    "ttl_seconds must be an integer >= 1"
                )

            expires_at = (
                current + timedelta(seconds=ttl_seconds)
            ).isoformat()

        raw_key = "dzk_" + secrets.token_urlsafe(40)
        key_id = "key_" + secrets.token_hex(12)

        record = APIKeyRecord(
            key_id=key_id,
            actor_id=identity.actor_id,
            organization_id=organization_id,
            key_fingerprint=_fingerprint(raw_key),
            created_at=current.isoformat(),
            expires_at=expires_at,
            enabled=True,
            scopes=normalized_scopes,
        )
        record.validate()
        self._api_keys[key_id] = record

        return record, raw_key

    def authenticate_api_key(
        self,
        *,
        key_id: str,
        raw_key: str,
        organization_id: str,
        required_scope: str,
        now: str | None = None,
    ) -> AuthenticatedPrincipal:
        record = self._api_keys.get(key_id)

        if record is None:
            raise AuthenticationError(
                "API key not found"
            )

        record.validate()

        if not record.enabled:
            raise AuthenticationError(
                "API key is disabled"
            )

        if record.organization_id != organization_id:
            raise AuthenticationError(
                "API key organization mismatch"
            )

        if (
            record.expires_at is not None
            and _now(now) >= _now(record.expires_at)
        ):
            raise AuthenticationError(
                "API key has expired"
            )

        if required_scope not in record.scopes:
            raise AuthenticationError(
                "API key missing required scope"
            )

        supplied = _fingerprint(raw_key)

        if not hmac.compare_digest(
            supplied,
            record.key_fingerprint,
        ):
            raise AuthenticationError(
                "API key credential mismatch"
            )

        identity = self.get_identity(record.actor_id)

        if not identity.enabled:
            raise AuthenticationError(
                "identity is disabled"
            )

        return AuthenticatedPrincipal(
            actor_id=identity.actor_id,
            actor_type=identity.actor_type,
            organization_id=identity.organization_id,
            authenticated=True,
            authentication_method="API_KEY",
            identity_ref=identity.identity_ref,
            session_ref=record.key_id,
            mfa_verified=False,
        )

    def disable_api_key(
        self,
        key_id: str,
    ) -> APIKeyRecord:
        record = self._api_keys.get(key_id)

        if record is None:
            raise AuthenticationError(
                "API key not found"
            )

        updated = replace(
            record,
            enabled=False,
        )
        self._api_keys[key_id] = updated
        return updated
