from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any, Callable


CAPABILITIES = {
    "AUTHORIZE",
    "CAPTURE",
    "REFUND",
}

SOURCE_TYPES = {
    "ORDER",
    "INVOICE",
}

CAPTURE_MODES = {
    "AUTHORIZE_ONLY",
    "AUTHORIZE_CAPTURE",
}

PROVIDER_OUTCOMES = {
    "AUTHORIZED",
    "CAPTURED",
    "FAILED",
    "CANCELLED",
}

KERNEL_PAYMENT_STATUSES = {
    "PENDING",
    "AUTHORIZED",
    "CAPTURED",
    "FAILED",
    "CANCELLED",
    "REFUNDED",
}

SECRET_REF_PATTERN = re.compile(
    r"(?:secret|vault|kms)://[A-Za-z0-9._~:/-]+"
)

ADAPTER_REF_PATTERN = re.compile(
    r"adapter://[A-Za-z0-9._~:/-]+"
)

CURRENCY_PATTERN = re.compile(r"[A-Z]{3}")
PROVIDER_ID_PATTERN = re.compile(r"[a-z][a-z0-9._-]{1,63}")

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
    "cardholder",
    "cvv",
    "cvc",
    "pan",
    "expiry",
}


class PaymentsBaaSError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    result = str(value).strip()
    if not result:
        raise PaymentsBaaSError(f"{name} must not be empty")
    return result


def _time(value: str | None = None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise PaymentsBaaSError("timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise PaymentsBaaSError("timestamp must be timezone-aware")
    return parsed


def _currency(value: str) -> str:
    result = str(value).strip().upper()
    if not CURRENCY_PATTERN.fullmatch(result):
        raise PaymentsBaaSError("currency must be three uppercase letters")
    return result


def _positive_minor(name: str, value: Any) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value <= 0
    ):
        raise PaymentsBaaSError(
            f"{name} must be an integer minor-unit amount > 0"
        )
    return value


def _canonical(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except (TypeError, ValueError) as exc:
        raise PaymentsBaaSError("value must be JSON-compatible") from exc


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
class ProviderConfiguration:
    provider_id: str
    adapter_ref: str
    credential_ref: str
    supported_currencies: tuple[str, ...]
    capabilities: tuple[str, ...]
    enabled: bool = True

    def validate(self) -> None:
        provider = str(self.provider_id).strip()
        if not PROVIDER_ID_PATTERN.fullmatch(provider):
            raise PaymentsBaaSError("provider_id must be a safe identifier")

        if not ADAPTER_REF_PATTERN.fullmatch(str(self.adapter_ref).strip()):
            raise PaymentsBaaSError("adapter_ref must use adapter://")

        if not SECRET_REF_PATTERN.fullmatch(str(self.credential_ref).strip()):
            raise PaymentsBaaSError(
                "credential_ref must use secret://, vault://, or kms://"
            )

        if not self.supported_currencies:
            raise PaymentsBaaSError("supported_currencies must not be empty")

        normalized_currencies = tuple(
            _currency(item) for item in self.supported_currencies
        )
        if len(normalized_currencies) != len(set(normalized_currencies)):
            raise PaymentsBaaSError("supported_currencies contains duplicates")

        if not self.capabilities:
            raise PaymentsBaaSError("capabilities must not be empty")

        if len(self.capabilities) != len(set(self.capabilities)):
            raise PaymentsBaaSError("capabilities contains duplicates")

        for capability in self.capabilities:
            if capability not in CAPABILITIES:
                raise PaymentsBaaSError(
                    f"unsupported provider capability: {capability}"
                )


@dataclass(frozen=True)
class PaymentRequest:
    payment_request_id: str
    source_type: str
    source_ref: str
    amount_minor: int
    currency: str
    capture_mode: str
    idempotency_key: str
    requested_at: str

    def validate(self) -> None:
        _text("payment_request_id", self.payment_request_id)

        if self.source_type not in SOURCE_TYPES:
            raise PaymentsBaaSError("unsupported source_type")

        _text("source_ref", self.source_ref)
        _positive_minor("amount_minor", self.amount_minor)
        _currency(self.currency)

        if self.capture_mode not in CAPTURE_MODES:
            raise PaymentsBaaSError("unsupported capture_mode")

        _text("idempotency_key", self.idempotency_key)
        _time(self.requested_at)


@dataclass(frozen=True)
class PaymentOperationPlan:
    payment_id: str
    provider_id: str
    provider_adapter_ref: str
    provider_credential_ref: str
    source_type: str
    source_ref: str
    amount_minor: int
    currency: str
    capture_mode: str
    idempotency_key: str
    tenant_context: dict[str, str]
    correlation_id: str
    kernel_authorization_ref: str
    desired_kernel_status: str
    audit_event: dict[str, Any]
    payment_event: dict[str, Any]
    state: str = "READY_FOR_PROVIDER_ADAPTER"


@dataclass(frozen=True)
class ProviderResult:
    payment_id: str
    provider_id: str
    provider_reference: str
    outcome: str
    amount_minor: int
    currency: str
    occurred_at: str
    error_code: str | None = None

    def validate(self) -> None:
        _text("payment_id", self.payment_id)

        if not PROVIDER_ID_PATTERN.fullmatch(str(self.provider_id).strip()):
            raise PaymentsBaaSError("invalid provider_id")

        _text("provider_reference", self.provider_reference)

        if self.outcome not in PROVIDER_OUTCOMES:
            raise PaymentsBaaSError("unsupported provider outcome")

        _positive_minor("amount_minor", self.amount_minor)
        _currency(self.currency)
        _time(self.occurred_at)

        if self.error_code is not None:
            code = _text("error_code", self.error_code)
            if len(code) > 128:
                raise PaymentsBaaSError("error_code exceeds 128 characters")

        if _contains_sensitive(self.__dict__):
            raise PaymentsBaaSError("provider result contains sensitive fields")


@dataclass(frozen=True)
class KernelTransitionPlan:
    payment_id: str
    provider_id: str
    provider_reference: str
    from_status: str
    transition_sequence: tuple[str, ...]
    amount_minor: int
    currency: str
    reconciliation_state: str
    audit_event: dict[str, Any]
    payment_event: dict[str, Any]
    state: str = "READY_FOR_KERNEL_TRANSACTION_ADAPTER"


@dataclass(frozen=True)
class RefundRequest:
    refund_id: str
    payment_id: str
    amount_minor: int
    currency: str
    reason: str
    idempotency_key: str
    requested_at: str

    def validate(self) -> None:
        _text("refund_id", self.refund_id)
        _text("payment_id", self.payment_id)
        _positive_minor("amount_minor", self.amount_minor)
        _currency(self.currency)
        _text("reason", self.reason)
        _text("idempotency_key", self.idempotency_key)
        _time(self.requested_at)


@dataclass(frozen=True)
class RefundOperationPlan:
    refund_id: str
    payment_id: str
    provider_id: str
    provider_reference: str
    provider_adapter_ref: str
    provider_credential_ref: str
    amount_minor: int
    currency: str
    reason: str
    idempotency_key: str
    tenant_context: dict[str, str]
    correlation_id: str
    kernel_authorization_ref: str
    audit_event: dict[str, Any]
    payment_event: dict[str, Any]
    state: str = "READY_FOR_PROVIDER_REFUND_ADAPTER"


@dataclass(frozen=True)
class ReconciliationResult:
    payment_id: str
    state: str
    checks: dict[str, bool]
    mismatch_fields: tuple[str, ...]


class PaymentAbstractionService:
    def __init__(
        self,
        *,
        kernel_transition_validator: Callable[
            [str, str, str, str, int, str],
            bool,
        ],
        kernel_refund_validator: Callable[
            [str, int, str, int, int, str],
            bool,
        ],
    ) -> None:
        if not callable(kernel_transition_validator):
            raise PaymentsBaaSError("kernel_transition_validator must be callable")
        if not callable(kernel_refund_validator):
            raise PaymentsBaaSError("kernel_refund_validator must be callable")

        self._kernel_transition_validator = kernel_transition_validator
        self._kernel_refund_validator = kernel_refund_validator
        self._providers: dict[str, ProviderConfiguration] = {}
        self._payment_tenants: dict[str, TenantScope] = {}
        self._payment_requests: dict[str, PaymentRequest] = {}
        self._payment_provider: dict[str, str] = {}
        self._payment_provider_ref: dict[str, str] = {}
        self._idempotency: dict[
            tuple[str, str, str, str],
            tuple[str, str],
        ] = {}
        self._refund_idempotency: dict[
            tuple[str, str, str],
            tuple[str, str],
        ] = {}

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

        if str(request_context.service).strip() != "payments":
            raise PaymentsBaaSError(
                "PaymentAbstractionService requires service=payments"
            )

        if not str(request_context.kernel_authorization_ref).startswith(
            "kernel_auth_"
        ):
            raise PaymentsBaaSError(
                "payment operations require Kernel authorization evidence"
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

    def register_provider(
        self,
        *,
        provider: ProviderConfiguration,
        request_context: Any,
    ) -> None:
        self._validate_request_context(request_context)
        provider.validate()

        if provider.provider_id in self._providers:
            raise PaymentsBaaSError("provider already registered")

        self._providers[provider.provider_id] = provider

    def create_payment_plan(
        self,
        *,
        provider_id: str,
        request: PaymentRequest,
        request_context: Any,
    ) -> dict[str, Any]:
        self._validate_request_context(request_context)
        request.validate()

        provider = self._require_provider(provider_id)

        if request.currency not in provider.supported_currencies:
            raise PaymentsBaaSError("provider does not support payment currency")

        required = (
            {"AUTHORIZE"}
            if request.capture_mode == "AUTHORIZE_ONLY"
            else {"AUTHORIZE", "CAPTURE"}
        )

        if not required.issubset(set(provider.capabilities)):
            raise PaymentsBaaSError(
                "provider lacks required payment capabilities"
            )

        tenant = self._tenant_from_context(request_context)

        canonical_request = {
            "organization_id": tenant.organization_id,
            "workspace_id": tenant.workspace_id,
            "project_id": tenant.project_id,
            "environment_id": tenant.environment_id,
            "provider_id": provider.provider_id,
            "source_type": request.source_type,
            "source_ref": request.source_ref,
            "amount_minor": request.amount_minor,
            "currency": request.currency,
            "capture_mode": request.capture_mode,
        }

        request_hash = sha256(
            _canonical(canonical_request).encode("utf-8")
        ).hexdigest()

        idem_key = (
            tenant.organization_id,
            tenant.environment_id,
            provider.provider_id,
            request.idempotency_key,
        )

        existing = self._idempotency.get(idem_key)

        if existing is not None:
            existing_hash, payment_id = existing
            if existing_hash != request_hash:
                raise PaymentsBaaSError(
                    "idempotency key reused with different payment request"
                )

            return {
                "created": False,
                "plan": self._build_payment_plan(
                    payment_id=payment_id,
                    provider=provider,
                    request=self._payment_requests[payment_id],
                    tenant=self._payment_tenants[payment_id],
                    request_context=request_context,
                ),
            }

        payment_id = (
            "payment_"
            + sha256(
                _canonical(
                    {
                        "idempotency_scope": idem_key,
                        "request_hash": request_hash,
                    }
                ).encode("utf-8")
            ).hexdigest()[:24]
        )

        self._payment_tenants[payment_id] = tenant
        self._payment_requests[payment_id] = request
        self._payment_provider[payment_id] = provider.provider_id
        self._idempotency[idem_key] = (request_hash, payment_id)

        return {
            "created": True,
            "plan": self._build_payment_plan(
                payment_id=payment_id,
                provider=provider,
                request=request,
                tenant=tenant,
                request_context=request_context,
            ),
        }

    def plan_provider_result(
        self,
        *,
        result: ProviderResult,
        kernel_current_status: str,
        request_context: Any,
    ) -> KernelTransitionPlan:
        self._validate_request_context(request_context)
        result.validate()

        request = self._require_payment(result.payment_id, request_context)
        expected_provider = self._payment_provider[result.payment_id]

        if result.provider_id != expected_provider:
            raise PaymentsBaaSError("provider result provider mismatch")

        if (
            result.amount_minor != request.amount_minor
            or result.currency != request.currency
        ):
            raise PaymentsBaaSError(
                "provider result amount/currency mismatch"
            )

        current = str(kernel_current_status).strip().upper()

        if current not in KERNEL_PAYMENT_STATUSES:
            raise PaymentsBaaSError("invalid Kernel payment status")

        sequence = self._transition_sequence(
            current=current,
            outcome=result.outcome,
        )

        prior = current
        for target in sequence:
            accepted = self._kernel_transition_validator(
                prior,
                target,
                result.payment_id,
                request.source_ref,
                request.amount_minor,
                request.currency,
            )
            if not accepted:
                raise PaymentsBaaSError(
                    f"Kernel rejected payment transition: {prior} -> {target}"
                )
            prior = target

        self._payment_provider_ref[result.payment_id] = result.provider_reference

        reconciliation_state = (
            "MATCH"
            if result.outcome == sequence[-1]
            else "TRANSITION_PATH_REQUIRED"
        )

        tenant = self._payment_tenants[result.payment_id]

        return KernelTransitionPlan(
            payment_id=result.payment_id,
            provider_id=result.provider_id,
            provider_reference=result.provider_reference,
            from_status=current,
            transition_sequence=sequence,
            amount_minor=result.amount_minor,
            currency=result.currency,
            reconciliation_state=reconciliation_state,
            audit_event={
                "audit_id": "audit_payment_" + result.payment_id.removeprefix("payment_"),
                "organization_id": tenant.organization_id,
                "actor_type": request_context.actor_type,
                "actor_id": request_context.actor_id,
                "action": "payments.provider_result.plan",
                "resource_type": "payment",
                "resource_id": result.payment_id,
                "timestamp": result.occurred_at,
                "correlation_id": request_context.correlation_id,
                "metadata": {
                    "provider_id": result.provider_id,
                    "provider_reference": result.provider_reference,
                    "from_status": current,
                    "transition_sequence": list(sequence),
                    "amount_minor": result.amount_minor,
                    "currency": result.currency,
                    "error_code": result.error_code,
                },
            },
            payment_event=self._payment_event(
                event_type="payment.provider_result_planned",
                payment_id=result.payment_id,
                request=request,
                tenant=tenant,
                request_context=request_context,
                occurred_at=result.occurred_at,
                payload={
                    "provider_id": result.provider_id,
                    "provider_reference": result.provider_reference,
                    "outcome": result.outcome,
                    "transition_sequence": list(sequence),
                    "error_code": result.error_code,
                },
            ),
        )

    def create_refund_plan(
        self,
        *,
        provider_id: str,
        provider_reference: str,
        request: RefundRequest,
        kernel_current_status: str,
        captured_amount_minor: int,
        previously_refunded_minor: int,
        request_context: Any,
    ) -> dict[str, Any]:
        self._validate_request_context(request_context)
        request.validate()

        payment_request = self._require_payment(
            request.payment_id,
            request_context,
        )
        provider = self._require_provider(provider_id)

        if self._payment_provider[request.payment_id] != provider.provider_id:
            raise PaymentsBaaSError("refund provider mismatch")

        if "REFUND" not in provider.capabilities:
            raise PaymentsBaaSError("provider does not support refunds")

        if str(kernel_current_status).strip().upper() != "CAPTURED":
            raise PaymentsBaaSError("refund requires CAPTURED Kernel payment")

        _positive_minor("captured_amount_minor", captured_amount_minor)

        if (
            not isinstance(previously_refunded_minor, int)
            or isinstance(previously_refunded_minor, bool)
            or previously_refunded_minor < 0
        ):
            raise PaymentsBaaSError(
                "previously_refunded_minor must be an integer >= 0"
            )

        if request.currency != payment_request.currency:
            raise PaymentsBaaSError("refund currency mismatch")

        accepted = self._kernel_refund_validator(
            request.payment_id,
            request.amount_minor,
            request.currency,
            captured_amount_minor,
            previously_refunded_minor,
            request.reason,
        )

        if not accepted:
            raise PaymentsBaaSError("Kernel rejected refund request")

        tenant = self._payment_tenants[request.payment_id]

        canonical_refund = {
            "payment_id": request.payment_id,
            "amount_minor": request.amount_minor,
            "currency": request.currency,
            "reason": request.reason,
            "provider_id": provider.provider_id,
            "provider_reference": provider_reference,
        }

        refund_hash = sha256(
            _canonical(canonical_refund).encode("utf-8")
        ).hexdigest()

        idem_key = (
            tenant.organization_id,
            request.payment_id,
            request.idempotency_key,
        )

        existing = self._refund_idempotency.get(idem_key)
        if existing is not None:
            existing_hash, existing_refund_id = existing
            if existing_hash != refund_hash:
                raise PaymentsBaaSError(
                    "refund idempotency key reused with different request"
                )
            if existing_refund_id != request.refund_id:
                raise PaymentsBaaSError(
                    "refund idempotency key reused with different refund_id"
                )

        self._refund_idempotency[idem_key] = (
            refund_hash,
            request.refund_id,
        )

        plan = RefundOperationPlan(
            refund_id=request.refund_id,
            payment_id=request.payment_id,
            provider_id=provider.provider_id,
            provider_reference=_text(
                "provider_reference",
                provider_reference,
            ),
            provider_adapter_ref=provider.adapter_ref,
            provider_credential_ref=provider.credential_ref,
            amount_minor=request.amount_minor,
            currency=request.currency,
            reason=request.reason,
            idempotency_key=request.idempotency_key,
            tenant_context={
                "organization_id": tenant.organization_id,
                "workspace_id": tenant.workspace_id,
                "project_id": tenant.project_id,
                "environment_id": tenant.environment_id,
            },
            correlation_id=request_context.correlation_id,
            kernel_authorization_ref=request_context.kernel_authorization_ref,
            audit_event={
                "audit_id": "audit_refund_" + request.refund_id,
                "organization_id": tenant.organization_id,
                "actor_type": request_context.actor_type,
                "actor_id": request_context.actor_id,
                "action": "payments.refund.plan",
                "resource_type": "refund",
                "resource_id": request.refund_id,
                "timestamp": request.requested_at,
                "correlation_id": request_context.correlation_id,
                "metadata": {
                    "payment_id": request.payment_id,
                    "provider_id": provider.provider_id,
                    "amount_minor": request.amount_minor,
                    "currency": request.currency,
                },
            },
            payment_event=self._payment_event(
                event_type="refund.provider_operation_planned",
                payment_id=request.payment_id,
                request=payment_request,
                tenant=tenant,
                request_context=request_context,
                occurred_at=request.requested_at,
                payload={
                    "refund_id": request.refund_id,
                    "provider_id": provider.provider_id,
                    "amount_minor": request.amount_minor,
                    "currency": request.currency,
                },
            ),
        )

        return {
            "created": existing is None,
            "plan": plan,
        }

    def reconcile(
        self,
        *,
        payment_id: str,
        kernel_status: str,
        kernel_amount_minor: int,
        kernel_currency: str,
        kernel_provider_reference: str | None,
        provider_status: str,
        provider_amount_minor: int,
        provider_currency: str,
        provider_reference: str,
        request_context: Any,
    ) -> ReconciliationResult:
        request = self._require_payment(payment_id, request_context)

        checks = {
            "amount": (
                kernel_amount_minor == provider_amount_minor == request.amount_minor
            ),
            "currency": (
                _currency(kernel_currency)
                == _currency(provider_currency)
                == request.currency
            ),
            "status": (
                str(kernel_status).strip().upper()
                == str(provider_status).strip().upper()
            ),
            "provider_reference": (
                kernel_provider_reference == provider_reference
            ),
        }

        mismatch = tuple(
            key
            for key, valid in checks.items()
            if not valid
        )

        return ReconciliationResult(
            payment_id=payment_id,
            state="MATCH" if not mismatch else "MISMATCH",
            checks=checks,
            mismatch_fields=mismatch,
        )

    def _build_payment_plan(
        self,
        *,
        payment_id: str,
        provider: ProviderConfiguration,
        request: PaymentRequest,
        tenant: TenantScope,
        request_context: Any,
    ) -> PaymentOperationPlan:
        return PaymentOperationPlan(
            payment_id=payment_id,
            provider_id=provider.provider_id,
            provider_adapter_ref=provider.adapter_ref,
            provider_credential_ref=provider.credential_ref,
            source_type=request.source_type,
            source_ref=request.source_ref,
            amount_minor=request.amount_minor,
            currency=request.currency,
            capture_mode=request.capture_mode,
            idempotency_key=request.idempotency_key,
            tenant_context={
                "organization_id": tenant.organization_id,
                "workspace_id": tenant.workspace_id,
                "project_id": tenant.project_id,
                "environment_id": tenant.environment_id,
            },
            correlation_id=request_context.correlation_id,
            kernel_authorization_ref=request_context.kernel_authorization_ref,
            desired_kernel_status="PENDING",
            audit_event={
                "audit_id": "audit_payment_plan_" + payment_id.removeprefix("payment_"),
                "organization_id": tenant.organization_id,
                "actor_type": request_context.actor_type,
                "actor_id": request_context.actor_id,
                "action": "payments.intent.plan",
                "resource_type": "payment",
                "resource_id": payment_id,
                "timestamp": request.requested_at,
                "correlation_id": request_context.correlation_id,
                "metadata": {
                    "provider_id": provider.provider_id,
                    "source_type": request.source_type,
                    "source_ref": request.source_ref,
                    "amount_minor": request.amount_minor,
                    "currency": request.currency,
                    "capture_mode": request.capture_mode,
                },
            },
            payment_event=self._payment_event(
                event_type="payment.intent_planned",
                payment_id=payment_id,
                request=request,
                tenant=tenant,
                request_context=request_context,
                occurred_at=request.requested_at,
                payload={
                    "provider_id": provider.provider_id,
                    "source_type": request.source_type,
                    "source_ref": request.source_ref,
                    "amount_minor": request.amount_minor,
                    "currency": request.currency,
                    "capture_mode": request.capture_mode,
                },
            ),
        )

    def _require_provider(self, provider_id: str) -> ProviderConfiguration:
        provider = self._providers.get(str(provider_id).strip())
        if provider is None:
            raise PaymentsBaaSError("payment provider not found")
        if not provider.enabled:
            raise PaymentsBaaSError("payment provider is disabled")
        return provider

    def _require_payment(
        self,
        payment_id: str,
        request_context: Any,
    ) -> PaymentRequest:
        self._validate_request_context(request_context)

        payment_id = str(payment_id).strip()
        request = self._payment_requests.get(payment_id)
        if request is None:
            raise PaymentsBaaSError("payment request not found")

        expected_tenant = self._payment_tenants[payment_id]
        actual_tenant = self._tenant_from_context(request_context)

        if not self._same_tenant(expected_tenant, actual_tenant):
            raise PaymentsBaaSError("cross-tenant payment access denied")

        return request

    @staticmethod
    def _transition_sequence(
        *,
        current: str,
        outcome: str,
    ) -> tuple[str, ...]:
        if current == outcome:
            raise PaymentsBaaSError("payment outcome does not advance state")

        if outcome == "CAPTURED" and current == "PENDING":
            return ("AUTHORIZED", "CAPTURED")

        if outcome == "AUTHORIZED" and current == "PENDING":
            return ("AUTHORIZED",)

        if outcome == "CAPTURED" and current == "AUTHORIZED":
            return ("CAPTURED",)

        if outcome in {"FAILED", "CANCELLED"} and current in {
            "PENDING",
            "AUTHORIZED",
        }:
            return (outcome,)

        raise PaymentsBaaSError(
            f"provider outcome cannot advance Kernel state: {current} -> {outcome}"
        )

    @staticmethod
    def _payment_event(
        *,
        event_type: str,
        payment_id: str,
        request: PaymentRequest,
        tenant: TenantScope,
        request_context: Any,
        occurred_at: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "event_type": event_type,
            "event_version": "1",
            "organization_id": tenant.organization_id,
            "workspace_id": tenant.workspace_id,
            "project_id": tenant.project_id,
            "environment_id": tenant.environment_id,
            "resource_type": "payment",
            "resource_id": payment_id,
            "occurred_at": occurred_at,
            "correlation_id": request_context.correlation_id,
            "actor_type": request_context.actor_type,
            "actor_id": request_context.actor_id,
            "payload": payload,
        }
