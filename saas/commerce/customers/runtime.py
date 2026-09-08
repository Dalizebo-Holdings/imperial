from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any


PII_POLICY_PATTERN = re.compile(
    r"pii-policy://[A-Za-z0-9._~:/-]+"
)

RETENTION_POLICY_PATTERN = re.compile(
    r"retention-policy://[A-Za-z0-9._~:/-]+"
)


class CommerceCustomersError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise CommerceCustomersError(
            f"{name} must not be empty"
        )
    result = str(value).strip()
    if not result:
        raise CommerceCustomersError(
            f"{name} must not be empty"
        )
    return result


def _time(value: str | None = None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CommerceCustomersError(
            "requested_at must be ISO-8601"
        ) from exc
    if parsed.tzinfo is None:
        raise CommerceCustomersError(
            "requested_at must be timezone-aware"
        )
    return parsed.isoformat()


def _validate_context(context: Any) -> None:
    if hasattr(context, "validate"):
        context.validate()

    if (
        str(getattr(context, "product", "")).strip().upper()
        != "COMMERCE"
    ):
        raise CommerceCustomersError(
            "Commerce Customers requires product=COMMERCE"
        )


def _assert_customer_evidence(
    *,
    context: Any,
    evidence: Any,
    customer_id: str,
) -> None:
    if evidence is None:
        raise CommerceCustomersError(
            "Customer Kernel authority evidence is required"
        )

    if hasattr(evidence, "validate"):
        evidence.validate()

    if str(getattr(evidence, "source", "")).strip() != "kernel.commerce":
        raise CommerceCustomersError(
            "authority evidence must come from kernel.commerce"
        )

    if (
        str(getattr(evidence, "entity_type", "")).strip().upper()
        != "CUSTOMER"
    ):
        raise CommerceCustomersError(
            "authority evidence entity_type mismatch"
        )

    if str(getattr(evidence, "entity_id", "")).strip() != customer_id:
        raise CommerceCustomersError(
            "authority evidence entity_id mismatch"
        )

    for name in [
        "organization_id",
        "workspace_id",
        "project_id",
        "environment_id",
    ]:
        if getattr(evidence, name, None) != getattr(context, name, None):
            raise CommerceCustomersError(
                "authority evidence tenant scope mismatch"
            )


def _normalize_email(value: str | None) -> str | None:
    if value is None:
        return None

    email = str(value).strip().lower()

    if not email:
        return None

    if len(email) > 320 or "@" not in email:
        raise CommerceCustomersError(
            "email has invalid basic shape"
        )

    local, domain = email.rsplit("@", 1)

    if not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
        raise CommerceCustomersError(
            "email has invalid basic shape"
        )

    return email


def _normalize_phone(value: str | None) -> str | None:
    if value is None:
        return None

    phone = str(value).strip()

    if not phone:
        return None

    if len(phone) > 64:
        raise CommerceCustomersError(
            "phone exceeds 64 characters"
        )

    return phone


def _validate_pii_refs(
    *,
    email: str | None,
    phone: str | None,
    pii_policy_ref: str | None,
    retention_policy_ref: str | None,
) -> None:
    if email is None and phone is None:
        return

    if not PII_POLICY_PATTERN.fullmatch(
        str(pii_policy_ref or "").strip()
    ):
        raise CommerceCustomersError(
            "contact PII requires pii-policy:// reference"
        )

    if not RETENTION_POLICY_PATTERN.fullmatch(
        str(retention_policy_ref or "").strip()
    ):
        raise CommerceCustomersError(
            "contact PII requires retention-policy:// reference"
        )


@dataclass(frozen=True)
class CustomerCreateRequest:
    customer_id: str
    display_name: str | None
    external_identity_ref: str | None
    email: str | None
    phone: str | None
    pii_policy_ref: str | None
    retention_policy_ref: str | None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("customer_id", self.customer_id)
        _text("idempotency_key", self.idempotency_key)

        display_name = (
            None
            if self.display_name is None
            else str(self.display_name).strip() or None
        )

        if display_name is not None and len(display_name) > 512:
            raise CommerceCustomersError(
                "display_name exceeds 512 characters"
            )

        external_identity_ref = (
            None
            if self.external_identity_ref is None
            else str(self.external_identity_ref).strip() or None
        )

        email = _normalize_email(self.email)
        phone = _normalize_phone(self.phone)

        _validate_pii_refs(
            email=email,
            phone=phone,
            pii_policy_ref=self.pii_policy_ref,
            retention_policy_ref=self.retention_policy_ref,
        )

        if (
            display_name is None
            and external_identity_ref is None
            and email is None
            and phone is None
        ):
            raise CommerceCustomersError(
                "Customer requires at least one profile field"
            )

        return {
            "display_name": display_name,
            "external_identity_ref": external_identity_ref,
            "email": email,
            "phone": phone,
            "pii_policy_ref": self.pii_policy_ref,
            "retention_policy_ref": self.retention_policy_ref,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class CustomerUpdateRequest:
    customer_id: str
    display_name: str | None
    external_identity_ref: str | None
    email: str | None
    phone: str | None
    pii_policy_ref: str | None
    retention_policy_ref: str | None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        return CustomerCreateRequest(
            customer_id=self.customer_id,
            display_name=self.display_name,
            external_identity_ref=self.external_identity_ref,
            email=self.email,
            phone=self.phone,
            pii_policy_ref=self.pii_policy_ref,
            retention_policy_ref=self.retention_policy_ref,
            idempotency_key=self.idempotency_key,
            requested_at=self.requested_at,
        ).normalized()


class CommerceCustomersService:
    def __init__(
        self,
        *,
        foundation: Any,
        product_command_type: Any,
    ) -> None:
        self._foundation = foundation
        self._product_command_type = product_command_type

    def plan_create(
        self,
        *,
        context: Any,
        request: CustomerCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()

        contact_fields = [
            name
            for name in ["email", "phone"]
            if normalized[name] is not None
        ]

        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="CUSTOMER",
                entity_id=request.customer_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": (
                        "PERSONAL_DATA"
                        if contact_fields
                        else "CUSTOMER_PROFILE"
                    ),
                    "sensitive_contact_fields": contact_fields,
                    "audit_logging_policy": (
                        "DO_NOT_LOG_CONTACT_VALUES"
                    ),
                    "persistence_hardening_status": (
                        "REQUIRES_PRODUCTION_PII_ADAPTER"
                        if contact_fields
                        else "NOT_APPLICABLE"
                    ),
                },
            )
        )

    def plan_update(
        self,
        *,
        context: Any,
        customer_evidence: Any,
        request: CustomerUpdateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)

        _assert_customer_evidence(
            context=context,
            evidence=customer_evidence,
            customer_id=request.customer_id,
        )

        normalized = request.normalized()

        contact_fields = [
            name
            for name in ["email", "phone"]
            if normalized[name] is not None
        ]

        return self._foundation.plan(
            self._product_command_type(
                action="UPDATE",
                entity_type="CUSTOMER",
                entity_id=request.customer_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": (
                        "PERSONAL_DATA"
                        if contact_fields
                        else "CUSTOMER_PROFILE"
                    ),
                    "sensitive_contact_fields": contact_fields,
                    "audit_logging_policy": (
                        "DO_NOT_LOG_CONTACT_VALUES"
                    ),
                    "persistence_hardening_status": (
                        "REQUIRES_PRODUCTION_PII_ADAPTER"
                        if contact_fields
                        else "NOT_APPLICABLE"
                    ),
                },
            )
        )
