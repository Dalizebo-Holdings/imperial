from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any

CONVERSION_STATES = {"PENDING", "CONFIRMED", "VOIDED", "RECOVERY_SCHEDULED", "RESOLVED"}

CONVERSION_TRANSITIONS = {
    "PENDING": {"CONFIRMED", "VOIDED", "RECOVERY_SCHEDULED"},
    "CONFIRMED": {"RESOLVED"},
    "VOIDED": {"RESOLVED"},
    "RECOVERY_SCHEDULED": {"RESOLVED"},
    "RESOLVED": set(),
}

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

CURRENCY_PATTERN = re.compile(r"[A-Z]{3}")
CONVERSION_ID_PATTERN = re.compile(r"[a-z][a-z0-9._-]{1,63}")


class CurrencyConversionBaaSError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    result = str(value).strip()
    if not result:
        raise CurrencyConversionBaaSError(f"{name} must not be empty")
    return result


def _time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CurrencyConversionBaaSError("timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise CurrencyConversionBaaSError("timestamp must be timezone-aware")
    return parsed


def _currency(value: str) -> str:
    result = str(value).strip().upper()
    if not CURRENCY_PATTERN.fullmatch(result):
        raise CurrencyConversionBaaSError("currency must be three uppercase letters")
    return result


def _minor(name: str, value: Any, *, allow_zero: bool = True) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise CurrencyConversionBaaSError(f"{name} must be an integer minor-unit amount")
    if value < 0 or (not allow_zero and value == 0):
        comparator = "> 0" if not allow_zero else ">= 0"
        raise CurrencyConversionBaaSError(f"{name} must be {comparator}")
    return value


def _percentage(name: str, value: Any) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise CurrencyConversionBaaSError(f"{name} must be a number")
    if value < 0:
        raise CurrencyConversionBaaSError(f"{name} must be >= 0")
    return float(value)


def _canonical(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except (TypeError, ValueError) as exc:
        raise CurrencyConversionBaaSError("value must be JSON-compatible") from exc


def _contains_sensitive(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).strip().lower() in SENSITIVE_KEYS:
                return True
            if _contains_sensitive(item):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_sensitive(item) for item in value)
    return False


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
class ConversionRequest:
    conversion_id: str
    source_currency: str
    destination_currency: str
    source_amount_minor: int
    destination_amount_minor: int
    conversion_fee_percentage: float
    conversion_fee_cap_percentage: float
    source_payment_id: str
    destination_payment_id: str
    idempotency_key: str
    requested_at: str

    def validate(self) -> None:
        _text("conversion_id", self.conversion_id)
        if not CONVERSION_ID_PATTERN.fullmatch(self.conversion_id):
            raise CurrencyConversionBaaSError("conversion_id must be a safe identifier")
        _currency(self.source_currency)
        _currency(self.destination_currency)
        _minor("source_amount_minor", self.source_amount_minor, allow_zero=False)
        _minor("destination_amount_minor", self.destination_amount_minor, allow_zero=False)
        _percentage("conversion_fee_percentage", self.conversion_fee_percentage)
        _percentage("conversion_fee_cap_percentage", self.conversion_fee_cap_percentage)
        _text("source_payment_id", self.source_payment_id)
        _text("destination_payment_id", self.destination_payment_id)
        _text("idempotency_key", self.idempotency_key)
        _time(self.requested_at)


@dataclass(frozen=True)
class ConversionOperationPlan:
    conversion_id: str
    tenant_context: dict[str, str]
    correlation_id: str
    kernel_authorization_ref: str
    source_currency: str
    destination_currency: str
    source_amount_minor: int
    destination_amount_minor: int
    conversion_fee_percentage: float
    conversion_fee_cap_percentage: float
    conversion_fee_minor: int
    confirmed_amount_minor: int
    source_payment_id: str
    destination_payment_id: str
    requested_at: str
    audit_event: dict[str, Any]
    conversion_event: dict[str, Any]
    state: str = "READY_FOR_CONVERSION_EXECUTOR"


class CurrencyConversionService:
    def __init__(self) -> None:
        self._conversions: dict[str, dict[str, Any]] = {}
        self._idempotency: dict[tuple[str, str], tuple[str, str]] = {}
        self._apology_credits: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _validate_request_context(request_context: Any) -> None:
        if hasattr(request_context, "validate"):
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
            "actor_type",
            "kernel_authorization_ref",
        ]:
            _text(name, getattr(request_context, name, None))
        if str(request_context.service).strip() != "currency_conversion":
            raise CurrencyConversionBaaSError(
                "CurrencyConversionService requires service=currency_conversion"
            )
        if not str(request_context.kernel_authorization_ref).startswith(
            "kernel_auth_"
        ):
            raise CurrencyConversionBaaSError(
                "conversion operations require Kernel authorization evidence"
            )

    @staticmethod
    def _tenant_from_context(request_context: Any) -> TenantScope:
        tenant = TenantScope(
            organization_id=request_context.organization_id,
            workspace_id=request_context.workspace_id,
            project_id=request_context.project_id,
            environment_id=request_context.environment_id,
        )
        tenant.validate()
        return tenant

    @staticmethod
    def _same_tenant(left: TenantScope, right: TenantScope) -> bool:
        return (
            left.organization_id == right.organization_id
            and left.workspace_id == right.workspace_id
            and left.project_id == right.project_id
            and left.environment_id == right.environment_id
        )

    def plan_conversion(
        self,
        *,
        request: ConversionRequest,
        request_context: Any,
    ) -> dict[str, Any]:
        self._validate_request_context(request_context)
        request.validate()

        tenant = self._tenant_from_context(request_context)

        canonical_request = {
            "organization_id": tenant.organization_id,
            "workspace_id": tenant.workspace_id,
            "project_id": tenant.project_id,
            "environment_id": tenant.environment_id,
            "conversion_id": request.conversion_id,
            "source_currency": request.source_currency,
            "destination_currency": request.destination_currency,
            "source_amount_minor": request.source_amount_minor,
            "destination_amount_minor": request.destination_amount_minor,
            "conversion_fee_percentage": request.conversion_fee_percentage,
            "conversion_fee_cap_percentage": request.conversion_fee_cap_percentage,
        }

        request_hash = sha256(
            _canonical(canonical_request).encode("utf-8")
        ).hexdigest()

        idem_key = (
            tenant.organization_id,
            request.idempotency_key,
        )

        existing = self._idempotency.get(idem_key)
        if existing is not None:
            existing_hash, existing_conversion_id = existing
            if existing_hash != request_hash:
                raise CurrencyConversionBaaSError(
                    "idempotency key reused with different conversion request"
                )
            conversion = self._conversions[existing_conversion_id]
            return {
                "created": False,
                "plan": self._build_plan(conversion, tenant, request_context),
            }

        conversion_fee_minor = _conversion_fee_minor(
            request.conversion_fee_percentage,
            request.destination_amount_minor,
        )

        if conversion_fee_minor < 0:
            raise CurrencyConversionBaaSError("conversion fee must be non-negative")

        if request.conversion_fee_cap_percentage < 0:
            raise CurrencyConversionBaaSError("conversion fee cap must be non-negative")

        allowed_fee = int(
            float(request.destination_amount_minor)
            * request.conversion_fee_cap_percentage
            / 100.0
        )
        if conversion_fee_minor > allowed_fee:
            raise CurrencyConversionBaaSError(
                "conversion fee exceeds cap percentage"
            )

        confirmed_amount_minor = request.destination_amount_minor + conversion_fee_minor

        if request.source_amount_minor != confirmed_amount_minor:
            raise CurrencyConversionBaaSError(
                "source amount must equal destination amount plus conversion fee"
            )

        conversion_id = request.conversion_id

        conversion = {
            "conversion_id": conversion_id,
            "tenant": tenant,
            "source_currency": request.source_currency,
            "destination_currency": request.destination_currency,
            "source_amount_minor": request.source_amount_minor,
            "destination_amount_minor": request.destination_amount_minor,
            "conversion_fee_percentage": request.conversion_fee_percentage,
            "conversion_fee_cap_percentage": request.conversion_fee_cap_percentage,
            "conversion_fee_minor": conversion_fee_minor,
            "confirmed_amount_minor": confirmed_amount_minor,
            "source_payment_id": request.source_payment_id,
            "destination_payment_id": request.destination_payment_id,
            "source_refund_id": None,
            "destination_refund_id": None,
            "apology_credit_id": None,
            "state": "PENDING",
            "idempotency_key": request.idempotency_key,
            "requested_at": request.requested_at,
            "confirmed_at": None,
            "escrow_feedback_at": None,
            "resolved_at": None,
            "resolution": None,
            "provider_reference": None,
            "kernel_authorization_ref": request_context.kernel_authorization_ref,
            "correlation_id": request_context.correlation_id,
        }

        self._conversions[conversion_id] = conversion
        self._idempotency[idem_key] = (request_hash, conversion_id)

        return {
            "created": True,
            "plan": self._build_plan(conversion, tenant, request_context),
        }

    def apply_settlement_callback(
        self,
        *,
        conversion_id: str,
        callback_type: str,
        callback_at: str,
        provider_reference: str | None,
        request_context: Any,
    ) -> dict[str, Any]:
        self._validate_request_context(request_context)

        conversion = self._require_conversion(conversion_id, request_context)

        current = conversion["state"]
        if current not in CONVERSION_STATES:
            raise CurrencyConversionBaaSError("conversion state is invalid")

        if callback_type == "confirmation":
            if current != "PENDING":
                raise CurrencyConversionBaaSError(
                    "confirmation callback requires PENDING conversion"
                )
            now = _time(callback_at).isoformat()
            conversion["state"] = "CONFIRMED"
            conversion["confirmed_at"] = now
            conversion["provider_reference"] = provider_reference
            return {
                "conversion_id": conversion_id,
                "state": "CONFIRMED",
                "conversion_event": self._conversion_event(
                    conversion,
                    request_context,
                    "conversion.confirmed",
                    now,
                ),
                "audit_event": self._audit_event(
                    conversion,
                    request_context,
                    "conversion.confirmed",
                    now,
                ),
            }

        if callback_type == "void":
            if current != "PENDING":
                raise CurrencyConversionBaaSError(
                    "void callback requires PENDING conversion"
                )
            now = _time(callback_at).isoformat()
            conversion["state"] = "VOIDED"
            conversion["provider_reference"] = provider_reference
            return {
                "conversion_id": conversion_id,
                "state": "VOIDED",
                "conversion_event": self._conversion_event(
                    conversion,
                    request_context,
                    "conversion.voided",
                    now,
                ),
                "audit_event": self._audit_event(
                    conversion,
                    request_context,
                    "conversion.voided",
                    now,
                ),
            }

        raise CurrencyConversionBaaSError(
            f"unsupported settlement callback: {callback_type}"
        )

    def apply_failed_transaction(
        self,
        *,
        conversion_id: str,
        provider_result_outcome: str,
        provider_reference: str | None,
        request_context: Any,
    ) -> dict[str, Any]:
        self._validate_request_context(request_context)

        conversion = self._require_conversion(conversion_id, request_context)

        if conversion["state"] != "PENDING":
            raise CurrencyConversionBaaSError(
                "failed transaction recovery requires PENDING conversion"
            )

        if provider_result_outcome not in {"FAILED", "CANCELLED"}:
            raise CurrencyConversionBaaSError(
                "failed transaction recovery is only allowed for FAILED or CANCELLED outcomes"
            )

        now = datetime.now(timezone.utc).isoformat()
        conversion["state"] = "RECOVERY_SCHEDULED"
        conversion["provider_reference"] = provider_reference
        conversion["resolved_at"] = now
        conversion["resolution"] = "FAILED_TRANSACTION_RECOVERY"

        refund_plan = None
        apology_credit_plan = None

        if conversion["source_payment_id"]:
            refund_plan = {
                "conversion_id": conversion_id,
                "refund_id": "refund_" + conversion_id,
                "payment_id": conversion["source_payment_id"],
                "state": "REFUND_PATH_SCHEDULED",
                "reason": "conversion failed transaction recovery",
            }

        if conversion["destination_payment_id"]:
            apology_credit_plan = self._create_apology_credit_plan(
                conversion,
                request_context,
                now,
            )

        return {
            "conversion_id": conversion_id,
            "state": "RECOVERY_SCHEDULED",
            "conversion_event": self._conversion_event(
                conversion,
                request_context,
                "conversion.recovery_scheduled",
                now,
            ),
            "audit_event": self._audit_event(
                conversion,
                request_context,
                "conversion.recovery_scheduled",
                now,
            ),
            "refund_plan": refund_plan,
            "apology_credit_plan": apology_credit_plan,
        }

    def resolve_conversion(
        self,
        *,
        conversion_id: str,
        escrow_feedback_at: str,
        resolved_at: str,
        provider_reference: str | None,
        request_context: Any,
    ) -> dict[str, Any]:
        self._validate_request_context(request_context)

        conversion = self._require_conversion(conversion_id, request_context)

        current = conversion["state"]
        if current not in {"CONFIRMED", "VOIDED", "RECOVERY_SCHEDULED"}:
            raise CurrencyConversionBaaSError(
                "resolution requires CONFIRMED, VOIDED, or RECOVERY_SCHEDULED conversion"
            )

        escrow = _time(escrow_feedback_at)
        resolved = _time(resolved_at)
        if escrow >= resolved:
            raise CurrencyConversionBaaSError(
                "escrow_feedback_at must be before resolved_at"
            )

        now = _time(resolved_at).isoformat()
        conversion["state"] = "RESOLVED"
        conversion["escrow_feedback_at"] = escrow_feedback_at
        conversion["resolved_at"] = now
        conversion["provider_reference"] = provider_reference
        conversion["resolution"] = (
            "CONFIRMED_RESOLVED"
            if current == "CONFIRMED"
            else "VOIDED_RESOLVED"
            if current == "VOIDED"
            else "RECOVERY_RESOLVED"
        )

        return {
            "conversion_id": conversion_id,
            "state": "RESOLVED",
            "conversion_event": self._conversion_event(
                conversion,
                request_context,
                "conversion.resolved",
                now,
            ),
            "audit_event": self._audit_event(
                conversion,
                request_context,
                "conversion.resolved",
                now,
            ),
        }

    def create_apology_credit(
        self,
        *,
        conversion_id: str,
        credit_id: str,
        reason: str,
        amount_minor: int,
        currency: str,
        issued_at: str,
        request_context: Any,
    ) -> dict[str, Any]:
        self._validate_request_context(request_context)

        conversion = self._require_conversion(conversion_id, request_context)

        if conversion["state"] != "RECOVERY_SCHEDULED":
            raise CurrencyConversionBaaSError(
                "apology credit creation requires RECOVERY_SCHEDULED conversion"
            )

        credit = {
            "credit_id": credit_id,
            "tenant": conversion["tenant"],
            "amount_minor": _minor("amount_minor", amount_minor, allow_zero=False),
            "currency": _currency(currency),
            "reason": _text("reason", reason),
            "issued_at": _time(issued_at).isoformat(),
            "conversion_id": conversion_id,
        }

        self._apology_credits[credit_id] = credit
        conversion["apology_credit_id"] = credit_id

        return {
            "credit_id": credit_id,
            "apology_credit_plan": {
                "credit_id": credit_id,
                "tenant_context": {
                    "organization_id": conversion["tenant"].organization_id,
                    "workspace_id": conversion["tenant"].workspace_id,
                    "project_id": conversion["tenant"].project_id,
                    "environment_id": conversion["tenant"].environment_id,
                },
                "amount_minor": credit["amount_minor"],
                "currency": credit["currency"],
                "reason": credit["reason"],
                "state": "READY_FOR_BILLING_CREDIT_APPLICATION",
            },
            "conversion_event": self._conversion_event(
                conversion,
                request_context,
                "conversion.apology_credit_issued",
                credit["issued_at"],
            ),
        }

    def reconcile_conversion(
        self,
        *,
        conversion_id: str,
        request_context: Any,
    ) -> dict[str, Any]:
        self._validate_request_context(request_context)

        conversion = self._require_conversion(conversion_id, request_context)

        checks: dict[str, Any] = {
            "tenant": True,
            "amount_balance": False,
            "fee_non_negative": False,
            "fee_cap": False,
            "fee_on_confirmed": False,
            "escrow_ordering": False,
            "state_machine": True,
            "callback_discipline": True,
        }

        tenant = conversion["tenant"]
        ctx_tenant = self._tenant_from_context(request_context)
        if not self._same_tenant(tenant, ctx_tenant):
            checks["tenant"] = False

        source = conversion["source_amount_minor"]
        destination = conversion["destination_amount_minor"]
        fee = conversion["conversion_fee_minor"]
        confirmed = conversion["confirmed_amount_minor"]
        current = conversion["state"]

        checks["amount_balance"] = source == destination + fee
        checks["fee_non_negative"] = fee >= 0
        checks["fee_on_confirmed"] = fee == _conversion_fee_minor(
            conversion["conversion_fee_percentage"],
            destination,
        )

        cap = conversion["conversion_fee_cap_percentage"]
        allowed_fee = int(
            float(confirmed) * cap / 100.0
        )
        checks["fee_cap"] = fee <= allowed_fee

        escrow = conversion["escrow_feedback_at"]
        resolved = conversion["resolved_at"]
        if escrow is not None and resolved is not None:
            checks["escrow_ordering"] = _time(escrow) < _time(resolved)
        else:
            checks["escrow_ordering"] = current == "RESOLVED" and False

        return {
            "conversion_id": conversion_id,
            "state": conversion["state"],
            "checks": checks,
            "valid": all(checks.values()),
        }

    def _require_conversion(self, conversion_id: str, request_context: Any) -> dict[str, Any]:
        self._validate_request_context(request_context)

        conversion = self._conversions.get(conversion_id)
        if conversion is None:
            raise CurrencyConversionBaaSError("conversion not found")

        if not self._same_tenant(
            conversion["tenant"],
            self._tenant_from_context(request_context),
        ):
            raise CurrencyConversionBaaSError("cross-tenant conversion access denied")

        return conversion

    def _build_plan(
        self,
        conversion: dict[str, Any],
        tenant: TenantScope,
        request_context: Any,
    ) -> ConversionOperationPlan:
        return ConversionOperationPlan(
            conversion_id=conversion["conversion_id"],
            tenant_context={
                "organization_id": tenant.organization_id,
                "workspace_id": tenant.workspace_id,
                "project_id": tenant.project_id,
                "environment_id": tenant.environment_id,
            },
            correlation_id=conversion["correlation_id"],
            kernel_authorization_ref=conversion["kernel_authorization_ref"],
            source_currency=conversion["source_currency"],
            destination_currency=conversion["destination_currency"],
            source_amount_minor=conversion["source_amount_minor"],
            destination_amount_minor=conversion["destination_amount_minor"],
            conversion_fee_percentage=conversion["conversion_fee_percentage"],
            conversion_fee_cap_percentage=conversion["conversion_fee_cap_percentage"],
            conversion_fee_minor=conversion["conversion_fee_minor"],
            confirmed_amount_minor=conversion["confirmed_amount_minor"],
            source_payment_id=conversion["source_payment_id"],
            destination_payment_id=conversion["destination_payment_id"],
            requested_at=conversion["requested_at"],
            audit_event=self._audit_event(
                conversion,
                request_context,
                "conversion.requested",
                conversion["requested_at"],
            ),
            conversion_event=self._conversion_event(
                conversion,
                request_context,
                "conversion.requested",
                conversion["requested_at"],
            ),
            state="READY_FOR_CONVERSION_EXECUTOR",
        )

    def _conversion_event(
        self,
        conversion: dict[str, Any],
        request_context: Any,
        event_type: str,
        occurred_at: str,
    ) -> dict[str, Any]:
        tenant = conversion["tenant"]
        return {
            "event_type": event_type,
            "event_version": "1",
            "organization_id": tenant.organization_id,
            "workspace_id": tenant.workspace_id,
            "project_id": tenant.project_id,
            "environment_id": tenant.environment_id,
            "resource_type": "conversion",
            "resource_id": conversion["conversion_id"],
            "occurred_at": occurred_at,
            "correlation_id": request_context.correlation_id,
            "actor_type": request_context.actor_type,
            "actor_id": request_context.actor_id,
            "payload": {
                "conversion_id": conversion["conversion_id"],
                "source_currency": conversion["source_currency"],
                "destination_currency": conversion["destination_currency"],
                "source_amount_minor": conversion["source_amount_minor"],
                "destination_amount_minor": conversion["destination_amount_minor"],
                "conversion_fee_minor": conversion["conversion_fee_minor"],
                "conversion_fee_percentage": conversion["conversion_fee_percentage"],
                "conversion_fee_cap_percentage": conversion[
                    "conversion_fee_cap_percentage"
                ],
                "confirmed_amount_minor": conversion["confirmed_amount_minor"],
                "state": conversion["state"],
            },
        }

    def _audit_event(
        self,
        conversion: dict[str, Any],
        request_context: Any,
        action: str,
        timestamp: str,
    ) -> dict[str, Any]:
        tenant = conversion["tenant"]
        return {
            "audit_id": "audit_conversion_" + conversion["conversion_id"],
            "organization_id": tenant.organization_id,
            "actor_type": request_context.actor_type,
            "actor_id": request_context.actor_id,
            "action": action,
            "resource_type": "conversion",
            "resource_id": conversion["conversion_id"],
            "timestamp": timestamp,
            "correlation_id": request_context.correlation_id,
            "metadata": {
                "source_currency": conversion["source_currency"],
                "destination_currency": conversion["destination_currency"],
                "source_amount_minor": conversion["source_amount_minor"],
                "destination_amount_minor": conversion["destination_amount_minor"],
                "state": conversion["state"],
            },
        }

    def _create_apology_credit_plan(
        self,
        conversion: dict[str, Any],
        request_context: Any,
        now: str,
    ) -> dict[str, Any]:
        return {
            "conversion_id": conversion["conversion_id"],
            "credit_id": "apology_credit_" + conversion["conversion_id"],
            "tenant_context": {
                "organization_id": conversion["tenant"].organization_id,
                "workspace_id": conversion["tenant"].workspace_id,
                "project_id": conversion["tenant"].project_id,
                "environment_id": conversion["tenant"].environment_id,
            },
            "amount_minor": 0,
            "currency": conversion["destination_currency"],
            "reason": "conversion failed transaction recovery",
            "state": "READY_FOR_BILLING_CREDIT_APPLICATION",
        }


def _conversion_fee_minor(
    percentage: float,
    confirmed_amount_minor: int,
) -> int:
    raw = float(confirmed_amount_minor) * percentage / 100.0
    return int(round(raw))


def _confirmed_amount_minor(
    destination_amount_minor: int,
    conversion_fee_minor: int,
) -> int:
    return destination_amount_minor
