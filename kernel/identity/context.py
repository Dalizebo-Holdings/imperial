from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any


ACTOR_TYPES = {
    "HUMAN_USER",
    "SERVICE_ACCOUNT",
    "API_CLIENT",
    "BACKGROUND_WORKER",
    "SYSTEM_ACTOR",
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
}


class IdentityContextError(ValueError):
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


@dataclass(frozen=True)
class IdentityContext:
    actor_id: str
    actor_type: str
    authenticated: bool
    authentication_method: str
    identity_ref: str
    session_ref: str | None = None
    mfa_verified: bool = False
    attributes: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not str(self.actor_id).strip():
            raise IdentityContextError("actor_id must not be empty")

        actor_type = str(self.actor_type).strip().upper()
        if actor_type not in ACTOR_TYPES:
            raise IdentityContextError(
                f"unsupported actor_type: {actor_type}"
            )

        if not str(self.authentication_method).strip():
            raise IdentityContextError(
                "authentication_method must not be empty"
            )

        if not str(self.identity_ref).strip():
            raise IdentityContextError(
                "identity_ref must not be empty"
            )

        try:
            json.dumps(
                self.attributes,
                sort_keys=True,
                separators=(",", ":"),
            )
        except (TypeError, ValueError) as exc:
            raise IdentityContextError(
                "attributes must be JSON-compatible"
            ) from exc

        if _contains_sensitive_key(self.attributes):
            raise IdentityContextError(
                "identity attributes contain a sensitive field"
            )
