from __future__ import annotations

from hashlib import sha256
import re
import uuid


class IdentifierError(ValueError):
    pass


def _validate_prefix(prefix: str) -> str:
    value = str(prefix).strip().lower()

    if not re.fullmatch(r"[a-z][a-z0-9_-]{1,31}", value):
        raise IdentifierError(
            "prefix must be 2-32 lowercase slug-like characters"
        )

    return value


def new_id(prefix: str) -> str:
    prefix = _validate_prefix(prefix)
    return f"{prefix}_{uuid.uuid4().hex}"


def stable_id(
    prefix: str,
    *,
    namespace: str,
    organization_id: str,
    operation: str,
    idempotency_key: str,
) -> str:
    prefix = _validate_prefix(prefix)

    required = {
        "namespace": namespace,
        "organization_id": organization_id,
        "operation": operation,
        "idempotency_key": idempotency_key,
    }

    missing = [
        name
        for name, value in required.items()
        if not str(value).strip()
    ]

    if missing:
        raise IdentifierError(
            "missing stable identifier inputs: "
            + ", ".join(missing)
        )

    material = "\x1f".join(
        [
            str(namespace).strip(),
            str(organization_id).strip(),
            str(operation).strip(),
            str(idempotency_key).strip(),
        ]
    ).encode("utf-8")

    digest = sha256(material).hexdigest()
    return f"{prefix}_{digest[:32]}"


def validate_id(
    value: str,
    *,
    expected_prefix: str | None = None,
) -> str:
    identifier = str(value).strip()

    if not re.fullmatch(
        r"[a-z][a-z0-9_-]{1,31}_[a-f0-9]{32}",
        identifier,
    ):
        raise IdentifierError(
            f"invalid Kernel identifier: {identifier}"
        )

    if expected_prefix is not None:
        prefix = _validate_prefix(expected_prefix)

        if not identifier.startswith(prefix + "_"):
            raise IdentifierError(
                f"identifier prefix mismatch: expected {prefix}"
            )

    return identifier
