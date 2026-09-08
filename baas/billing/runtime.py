from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any


BILLING_INTERVALS = {"MONTHLY", "YEARLY"}
PLAN_STATES = {"ACTIVE", "RETIRED"}
SUBSCRIPTION_STATES = {"ACTIVE", "PAST_DUE", "CANCELLED"}
INVOICE_STATES = {"DRAFT", "OPEN", "VOID"}
LINE_TYPES = {"RECURRING", "METERED", "CREDIT"}

SUBSCRIPTION_TRANSITIONS = {
    "ACTIVE": {"PAST_DUE", "CANCELLED"},
    "PAST_DUE": {"ACTIVE", "CANCELLED"},
    "CANCELLED": set(),
}

CURRENCY_PATTERN = re.compile(r"[A-Z]{3}")
METRIC_PATTERN = re.compile(r"[a-z][a-z0-9._-]{1,63}")
UNIT_PATTERN = re.compile(r"[a-z][a-z0-9._/-]{0,63}")


class BillingBaaSError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    result = str(value).strip()
    if not result:
        raise BillingBaaSError(f"{name} must not be empty")
    return result


def _time(value: str | None = None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise BillingBaaSError("timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise BillingBaaSError("timestamp must be timezone-aware")
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
        raise BillingBaaSError("value must be JSON-compatible") from exc


def _minor(name: str, value: Any, *, allow_zero: bool = True) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise BillingBaaSError(f"{name} must be an integer minor-unit amount")
    if value < 0 or (not allow_zero and value == 0):
        comparator = "> 0" if not allow_zero else ">= 0"
        raise BillingBaaSError(f"{name} must be {comparator}")
    return value


def _currency(value: str) -> str:
    result = str(value).strip().upper()
    if not CURRENCY_PATTERN.fullmatch(result):
        raise BillingBaaSError("currency must be a three-letter uppercase code")
    return result


def _decimal_quantity(value: str) -> Decimal:
    raw = _text("quantity", value)
    try:
        number = Decimal(raw)
    except InvalidOperation as exc:
        raise BillingBaaSError("quantity must be a decimal string") from exc
    if not number.is_finite() or number < 0:
        raise BillingBaaSError("quantity must be finite and non-negative")
    exponent = number.as_tuple().exponent
    if isinstance(exponent, int) and exponent < -18:
        raise BillingBaaSError("quantity supports at most 18 fractional digits")
    return number


def canonical_quantity(value: str) -> str:
    number = _decimal_quantity(value)
    result = format(number, "f")
    if "." in result:
        result = result.rstrip("0").rstrip(".")
    return result or "0"


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
class MeteredRate:
    metric: str
    unit: str
    unit_price_minor: int
    included_quantity: str = "0"

    def validate(self) -> None:
        if not METRIC_PATTERN.fullmatch(str(self.metric).strip()):
            raise BillingBaaSError("metric must be a safe identifier")
        if not UNIT_PATTERN.fullmatch(str(self.unit).strip()):
            raise BillingBaaSError("unit must be a safe identifier")
        _minor("unit_price_minor", self.unit_price_minor)
        if canonical_quantity(self.included_quantity) != self.included_quantity:
            raise BillingBaaSError("included_quantity must be canonical")


@dataclass(frozen=True)
class PlanVersion:
    plan_id: str
    version: int
    name: str
    currency: str
    billing_interval: str
    recurring_amount_minor: int
    metered_rates: tuple[MeteredRate, ...]
    entitlements: dict[str, Any]
    effective_at: str
    state: str = "ACTIVE"

    def validate(self) -> None:
        _text("plan_id", self.plan_id)
        _text("name", self.name)
        if not isinstance(self.version, int) or self.version < 1:
            raise BillingBaaSError("plan version must be >= 1")
        _currency(self.currency)
        if self.billing_interval not in BILLING_INTERVALS:
            raise BillingBaaSError("unsupported billing_interval")
        _minor("recurring_amount_minor", self.recurring_amount_minor)
        if self.state not in PLAN_STATES:
            raise BillingBaaSError("invalid plan state")
        _time(self.effective_at)
        keys = set()
        for rate in self.metered_rates:
            rate.validate()
            key = (rate.metric, rate.unit)
            if key in keys:
                raise BillingBaaSError("duplicate metered rate")
            keys.add(key)
        _canonical(self.entitlements)


@dataclass(frozen=True)
class Subscription:
    subscription_id: str
    tenant: TenantScope
    customer_ref: str
    plan_id: str
    plan_version: int
    status: str
    current_period_start: str
    current_period_end: str
    cancel_at_period_end: bool
    created_at: str
    updated_at: str

    def validate(self) -> None:
        _text("subscription_id", self.subscription_id)
        self.tenant.validate()
        _text("customer_ref", self.customer_ref)
        _text("plan_id", self.plan_id)
        if not isinstance(self.plan_version, int) or self.plan_version < 1:
            raise BillingBaaSError("plan_version must be >= 1")
        if self.status not in SUBSCRIPTION_STATES:
            raise BillingBaaSError("invalid subscription status")
        start = _time(self.current_period_start)
        end = _time(self.current_period_end)
        if start >= end:
            raise BillingBaaSError("subscription period start must be before end")
        _time(self.created_at)
        _time(self.updated_at)


@dataclass(frozen=True)
class UsageEvidence:
    aggregate_id: str
    tenant: TenantScope
    metric: str
    unit: str
    total_quantity: str
    event_count: int
    period_start: str
    period_end: str
    source_hash: str

    def validate(self) -> None:
        _text("aggregate_id", self.aggregate_id)
        self.tenant.validate()
        if not METRIC_PATTERN.fullmatch(str(self.metric).strip()):
            raise BillingBaaSError("invalid usage metric")
        if not UNIT_PATTERN.fullmatch(str(self.unit).strip()):
            raise BillingBaaSError("invalid usage unit")
        if canonical_quantity(self.total_quantity) != self.total_quantity:
            raise BillingBaaSError("usage total_quantity must be canonical")
        if not isinstance(self.event_count, int) or self.event_count < 0:
            raise BillingBaaSError("event_count must be >= 0")
        start = _time(self.period_start)
        end = _time(self.period_end)
        if start >= end:
            raise BillingBaaSError("usage period start must be before end")
        if not re.fullmatch(r"[a-f0-9]{64}", str(self.source_hash)):
            raise BillingBaaSError("usage source_hash must be SHA-256 hex")


@dataclass(frozen=True)
class CreditGrant:
    credit_id: str
    tenant: TenantScope
    amount_minor: int
    currency: str
    reason: str
    issued_at: str

    def validate(self) -> None:
        _text("credit_id", self.credit_id)
        self.tenant.validate()
        _minor("amount_minor", self.amount_minor, allow_zero=False)
        _currency(self.currency)
        _text("reason", self.reason)
        _time(self.issued_at)


@dataclass(frozen=True)
class InvoiceLine:
    line_id: str
    line_type: str
    description: str
    amount_minor: int
    metric: str | None = None
    unit: str | None = None
    quantity: str | None = None
    unit_price_minor: int | None = None
    usage_aggregate_id: str | None = None
    credit_id: str | None = None

    def validate(self) -> None:
        _text("line_id", self.line_id)
        if self.line_type not in LINE_TYPES:
            raise BillingBaaSError("invalid invoice line type")
        _text("description", self.description)
        if not isinstance(self.amount_minor, int) or isinstance(self.amount_minor, bool):
            raise BillingBaaSError("invoice line amount_minor must be integer")
        if self.line_type == "CREDIT":
            if self.amount_minor >= 0:
                raise BillingBaaSError("credit invoice line must be negative")
            _text("credit_id", self.credit_id)
        elif self.amount_minor < 0:
            raise BillingBaaSError("non-credit invoice line may not be negative")


@dataclass(frozen=True)
class Invoice:
    invoice_id: str
    subscription_id: str
    tenant: TenantScope
    plan_id: str
    plan_version: int
    currency: str
    period_start: str
    period_end: str
    lines: tuple[InvoiceLine, ...]
    subtotal_minor: int
    credit_minor: int
    total_minor: int
    usage_source_hash: str
    calculation_hash: str
    state: str
    created_at: str
    opened_at: str | None = None

    def validate(self) -> None:
        _text("invoice_id", self.invoice_id)
        _text("subscription_id", self.subscription_id)
        self.tenant.validate()
        _text("plan_id", self.plan_id)
        _currency(self.currency)
        if self.state not in INVOICE_STATES:
            raise BillingBaaSError("invalid invoice state")
        _minor("subtotal_minor", self.subtotal_minor)
        _minor("credit_minor", self.credit_minor)
        _minor("total_minor", self.total_minor)
        if self.total_minor != self.subtotal_minor - self.credit_minor:
            raise BillingBaaSError("invoice total invariant failed")
        if self.credit_minor > self.subtotal_minor:
            raise BillingBaaSError("invoice credit exceeds subtotal")
        for line in self.lines:
            line.validate()
        if not re.fullmatch(r"[a-f0-9]{64}", self.usage_source_hash):
            raise BillingBaaSError("usage_source_hash must be SHA-256 hex")
        if not re.fullmatch(r"[a-f0-9]{64}", self.calculation_hash):
            raise BillingBaaSError("calculation_hash must be SHA-256 hex")
        _time(self.created_at)
        if self.opened_at is not None:
            _time(self.opened_at)


@dataclass(frozen=True)
class PaymentRetryIntent:
    retry_id: str
    invoice_id: str
    attempt: int
    amount_minor: int
    currency: str
    idempotency_key: str
    kernel_authorization_ref: str
    audit_event: dict[str, Any]
    billing_event: dict[str, Any]
    state: str = "READY_FOR_PAYMENT_ABSTRACTION"


class SubscriptionBillingService:
    def __init__(self) -> None:
        self._plans: dict[tuple[str, int], PlanVersion] = {}
        self._subscriptions: dict[str, Subscription] = {}
        self._credits: dict[str, CreditGrant] = {}
        self._credit_remaining: dict[str, int] = {}
        self._invoices: dict[str, Invoice] = {}
        self._invoice_requests: dict[str, str] = {}

    @staticmethod
    def _validate_request_context(request_context: Any) -> None:
        if hasattr(request_context, "validate"):
            request_context.validate()
        for name in [
            "request_id", "correlation_id", "service", "operation",
            "organization_id", "workspace_id", "project_id", "environment_id",
            "actor_id", "actor_type", "kernel_authorization_ref",
        ]:
            _text(name, getattr(request_context, name, None))
        if str(request_context.service).strip() != "subscription_billing":
            raise BillingBaaSError(
                "SubscriptionBillingService requires service=subscription_billing"
            )
        if not str(request_context.kernel_authorization_ref).startswith("kernel_auth_"):
            raise BillingBaaSError(
                "billing operations require Kernel authorization evidence"
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

    def register_plan_version(
        self,
        *,
        plan: PlanVersion,
        request_context: Any,
    ) -> None:
        self._validate_request_context(request_context)
        plan.validate()
        key = (plan.plan_id, plan.version)
        if key in self._plans:
            raise BillingBaaSError("plan version already registered")
        self._plans[key] = plan

    def create_subscription(
        self,
        *,
        subscription_id: str,
        customer_ref: str,
        plan_id: str,
        plan_version: int,
        current_period_start: str,
        current_period_end: str,
        request_context: Any,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        self._validate_request_context(request_context)
        if subscription_id in self._subscriptions:
            raise BillingBaaSError("subscription already exists")
        plan = self._require_plan(plan_id, plan_version)
        if plan.state != "ACTIVE":
            raise BillingBaaSError("new subscription requires ACTIVE plan version")
        now = _time(created_at).isoformat()
        subscription = Subscription(
            subscription_id=_text("subscription_id", subscription_id),
            tenant=self._tenant_from_context(request_context),
            customer_ref=_text("customer_ref", customer_ref),
            plan_id=plan.plan_id,
            plan_version=plan.version,
            status="ACTIVE",
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            cancel_at_period_end=False,
            created_at=now,
            updated_at=now,
        )
        subscription.validate()
        self._subscriptions[subscription.subscription_id] = subscription
        return {
            "subscription": subscription,
            "billing_event": self._billing_event(
                "subscription.created",
                subscription.subscription_id,
                request_context,
                now,
                {"plan_id": plan.plan_id, "plan_version": plan.version},
            ),
        }

    def transition_subscription(
        self,
        *,
        subscription_id: str,
        target_status: str,
        request_context: Any,
        updated_at: str | None = None,
    ) -> dict[str, Any]:
        subscription = self._get_subscription(subscription_id, request_context)
        target = str(target_status).strip().upper()
        if target not in SUBSCRIPTION_STATES:
            raise BillingBaaSError("invalid target subscription status")
        if target not in SUBSCRIPTION_TRANSITIONS[subscription.status]:
            raise BillingBaaSError(
                f"illegal subscription transition: {subscription.status} -> {target}"
            )
        now = _time(updated_at).isoformat()
        updated = replace(subscription, status=target, updated_at=now)
        updated.validate()
        self._subscriptions[subscription_id] = updated
        return {
            "subscription": updated,
            "billing_event": self._billing_event(
                "subscription.status_changed",
                subscription_id,
                request_context,
                now,
                {"from": subscription.status, "to": target},
            ),
        }

    def issue_credit(
        self,
        *,
        credit: CreditGrant,
        request_context: Any,
    ) -> dict[str, Any]:
        self._validate_request_context(request_context)
        credit.validate()
        tenant = self._tenant_from_context(request_context)
        if not self._same_tenant(credit.tenant, tenant):
            raise BillingBaaSError("credit tenant scope mismatch")
        if credit.credit_id in self._credits:
            raise BillingBaaSError("credit already exists")
        self._credits[credit.credit_id] = credit
        self._credit_remaining[credit.credit_id] = credit.amount_minor
        return {
            "credit": credit,
            "billing_event": self._billing_event(
                "credit.issued",
                credit.credit_id,
                request_context,
                credit.issued_at,
                {
                    "amount_minor": credit.amount_minor,
                    "currency": credit.currency,
                },
            ),
        }

    def resolve_entitlements(
        self,
        *,
        subscription_id: str,
        request_context: Any,
    ) -> dict[str, Any]:
        subscription = self._get_subscription(subscription_id, request_context)
        if subscription.status == "CANCELLED":
            return {}
        plan = self._require_plan(subscription.plan_id, subscription.plan_version)
        return json.loads(_canonical(plan.entitlements))

    def generate_invoice(
        self,
        *,
        subscription_id: str,
        usage: tuple[UsageEvidence, ...],
        credit_ids: tuple[str, ...],
        request_context: Any,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        subscription = self._get_subscription(subscription_id, request_context)
        if subscription.status == "CANCELLED":
            raise BillingBaaSError("cancelled subscription cannot be invoiced")
        plan = self._require_plan(subscription.plan_id, subscription.plan_version)
        tenant = self._tenant_from_context(request_context)

        seen_aggregates: set[str] = set()
        usage_by_key: dict[tuple[str, str], list[UsageEvidence]] = {}
        for evidence in usage:
            evidence.validate()
            if not self._same_tenant(evidence.tenant, tenant):
                raise BillingBaaSError("usage evidence tenant mismatch")
            if evidence.aggregate_id in seen_aggregates:
                raise BillingBaaSError("duplicate usage aggregate")
            seen_aggregates.add(evidence.aggregate_id)
            if (
                evidence.period_start != subscription.current_period_start
                or evidence.period_end != subscription.current_period_end
            ):
                raise BillingBaaSError("usage period must match subscription period")
            usage_by_key.setdefault((evidence.metric, evidence.unit), []).append(evidence)

        rates = {(rate.metric, rate.unit): rate for rate in plan.metered_rates}
        for key in usage_by_key:
            if key not in rates:
                raise BillingBaaSError("usage evidence has no matching plan rate")

        if len(credit_ids) != len(set(credit_ids)):
            raise BillingBaaSError("duplicate credit_id")

        request_manifest = {
            "subscription_id": subscription.subscription_id,
            "period_start": subscription.current_period_start,
            "period_end": subscription.current_period_end,
            "plan_id": plan.plan_id,
            "plan_version": plan.version,
            "usage": [
                {
                    "aggregate_id": evidence.aggregate_id,
                    "source_hash": evidence.source_hash,
                    "metric": evidence.metric,
                    "unit": evidence.unit,
                    "total_quantity": evidence.total_quantity,
                }
                for evidence in sorted(
                    usage,
                    key=lambda item: item.aggregate_id,
                )
            ],
            "credit_ids": list(credit_ids),
        }
        request_fingerprint = sha256(
            _canonical(request_manifest).encode("utf-8")
        ).hexdigest()

        existing_invoice_id = self._invoice_requests.get(
            request_fingerprint
        )
        if existing_invoice_id is not None:
            return {
                "created": False,
                "invoice": self._invoices[existing_invoice_id],
                "billing_event": None,
            }

        lines: list[InvoiceLine] = []
        recurring_id = self._line_id(
            subscription.subscription_id,
            "RECURRING",
            plan.plan_id,
            str(plan.version),
        )
        lines.append(
            InvoiceLine(
                line_id=recurring_id,
                line_type="RECURRING",
                description=f"{plan.name} recurring charge",
                amount_minor=plan.recurring_amount_minor,
            )
        )

        source_hashes: list[str] = []
        for key in sorted(usage_by_key):
            rate = rates[key]
            for evidence in sorted(
                usage_by_key[key],
                key=lambda item: item.aggregate_id,
            ):
                billable = max(
                    Decimal("0"),
                    _decimal_quantity(evidence.total_quantity)
                    - _decimal_quantity(rate.included_quantity),
                )
                amount_decimal = billable * Decimal(rate.unit_price_minor)
                amount_minor = int(
                    amount_decimal.quantize(
                        Decimal("1"),
                        rounding=ROUND_HALF_UP,
                    )
                )
                line_id = self._line_id(
                    subscription.subscription_id,
                    "METERED",
                    evidence.aggregate_id,
                    str(plan.version),
                )
                lines.append(
                    InvoiceLine(
                        line_id=line_id,
                        line_type="METERED",
                        description=f"{evidence.metric} usage",
                        amount_minor=amount_minor,
                        metric=evidence.metric,
                        unit=evidence.unit,
                        quantity=canonical_quantity(str(billable)),
                        unit_price_minor=rate.unit_price_minor,
                        usage_aggregate_id=evidence.aggregate_id,
                    )
                )
                source_hashes.append(evidence.source_hash)

        subtotal = sum(line.amount_minor for line in lines)
        remaining_subtotal = subtotal
        credit_total = 0

        selected_credit_ids: list[str] = []
        for credit_id in credit_ids:
            selected_credit_ids.append(credit_id)
            credit = self._credits.get(credit_id)
            if credit is None:
                raise BillingBaaSError("credit not found")
            if not self._same_tenant(credit.tenant, tenant):
                raise BillingBaaSError("cross-tenant credit access denied")
            if credit.currency != plan.currency:
                raise BillingBaaSError("credit currency mismatch")
            available = self._credit_remaining[credit_id]
            applied = min(available, remaining_subtotal)
            if applied <= 0:
                continue
            lines.append(
                InvoiceLine(
                    line_id=self._line_id(
                        subscription.subscription_id,
                        "CREDIT",
                        credit_id,
                        str(plan.version),
                    ),
                    line_type="CREDIT",
                    description=credit.reason,
                    amount_minor=-applied,
                    credit_id=credit_id,
                )
            )
            credit_total += applied
            remaining_subtotal -= applied

        usage_source_hash = sha256(
            _canonical(sorted(source_hashes)).encode("utf-8")
        ).hexdigest()

        manifest = self._calculation_manifest(
            subscription=subscription,
            plan=plan,
            lines=tuple(lines),
            usage_source_hash=usage_source_hash,
        )
        calculation_hash = sha256(
            _canonical(manifest).encode("utf-8")
        ).hexdigest()

        invoice_id = (
            "invoice_"
            + sha256(
                _canonical(
                    {
                        "calculation_hash": calculation_hash,
                        "usage_ids": sorted(seen_aggregates),
                        "credit_ids": selected_credit_ids,
                    }
                ).encode("utf-8")
            ).hexdigest()[:24]
        )

        existing = self._invoices.get(invoice_id)
        if existing is not None:
            return {
                "created": False,
                "invoice": existing,
                "billing_event": None,
            }

        now = _time(created_at).isoformat()
        invoice = Invoice(
            invoice_id=invoice_id,
            subscription_id=subscription.subscription_id,
            tenant=tenant,
            plan_id=plan.plan_id,
            plan_version=plan.version,
            currency=plan.currency,
            period_start=subscription.current_period_start,
            period_end=subscription.current_period_end,
            lines=tuple(lines),
            subtotal_minor=subtotal,
            credit_minor=credit_total,
            total_minor=subtotal - credit_total,
            usage_source_hash=usage_source_hash,
            calculation_hash=calculation_hash,
            state="DRAFT",
            created_at=now,
        )
        invoice.validate()

        for line in invoice.lines:
            if line.line_type == "CREDIT" and line.credit_id:
                self._credit_remaining[line.credit_id] += line.amount_minor

        self._invoices[invoice_id] = invoice
        self._invoice_requests[
            request_fingerprint
        ] = invoice_id
        return {
            "created": True,
            "invoice": invoice,
            "billing_event": self._billing_event(
                "invoice.drafted",
                invoice_id,
                request_context,
                now,
                {
                    "subscription_id": subscription.subscription_id,
                    "plan_id": plan.plan_id,
                    "plan_version": plan.version,
                    "currency": plan.currency,
                    "total_minor": invoice.total_minor,
                    "usage_source_hash": usage_source_hash,
                    "calculation_hash": calculation_hash,
                },
            ),
        }

    def open_invoice(
        self,
        *,
        invoice_id: str,
        request_context: Any,
        opened_at: str | None = None,
    ) -> dict[str, Any]:
        invoice = self._get_invoice(invoice_id, request_context)
        if invoice.state != "DRAFT":
            raise BillingBaaSError("only DRAFT invoices may be opened")
        now = _time(opened_at).isoformat()
        updated = replace(invoice, state="OPEN", opened_at=now)
        updated.validate()
        self._invoices[invoice_id] = updated
        return {
            "invoice": updated,
            "billing_event": self._billing_event(
                "invoice.opened",
                invoice_id,
                request_context,
                now,
                {
                    "amount_minor": updated.total_minor,
                    "currency": updated.currency,
                },
            ),
        }

    def create_payment_retry_intent(
        self,
        *,
        invoice_id: str,
        attempt: int,
        request_context: Any,
    ) -> PaymentRetryIntent:
        invoice = self._get_invoice(invoice_id, request_context)
        if invoice.state != "OPEN":
            raise BillingBaaSError("payment retry requires OPEN invoice")
        if not isinstance(attempt, int) or attempt < 1 or attempt > 25:
            raise BillingBaaSError("payment retry attempt must be 1..25")
        idempotency_key = (
            f"billing:{invoice.invoice_id}:payment-retry:{attempt}"
        )
        retry_id = (
            "billing_retry_"
            + sha256(idempotency_key.encode("utf-8")).hexdigest()[:24]
        )
        now = datetime.now(timezone.utc).isoformat()
        event = self._billing_event(
            "payment_retry.requested",
            retry_id,
            request_context,
            now,
            {
                "invoice_id": invoice.invoice_id,
                "attempt": attempt,
                "amount_minor": invoice.total_minor,
                "currency": invoice.currency,
            },
        )
        audit = {
            "audit_id": "audit_" + retry_id,
            "organization_id": invoice.tenant.organization_id,
            "actor_type": request_context.actor_type,
            "actor_id": request_context.actor_id,
            "action": "subscription_billing.payment_retry.request",
            "resource_type": "invoice",
            "resource_id": invoice.invoice_id,
            "timestamp": now,
            "correlation_id": request_context.correlation_id,
            "metadata": {
                "retry_id": retry_id,
                "attempt": attempt,
                "amount_minor": invoice.total_minor,
                "currency": invoice.currency,
                "kernel_authorization_ref": (
                    request_context.kernel_authorization_ref
                ),
            },
        }
        return PaymentRetryIntent(
            retry_id=retry_id,
            invoice_id=invoice.invoice_id,
            attempt=attempt,
            amount_minor=invoice.total_minor,
            currency=invoice.currency,
            idempotency_key=idempotency_key,
            kernel_authorization_ref=request_context.kernel_authorization_ref,
            audit_event=audit,
            billing_event=event,
        )

    def reconcile_invoice(
        self,
        *,
        invoice_id: str,
        usage: tuple[UsageEvidence, ...],
        request_context: Any,
    ) -> dict[str, Any]:
        invoice = self._get_invoice(invoice_id, request_context)
        subscription = self._get_subscription(
            invoice.subscription_id,
            request_context,
        )
        plan = self._require_plan(invoice.plan_id, invoice.plan_version)

        evidence_by_id = {}
        for item in usage:
            item.validate()
            evidence_by_id[item.aggregate_id] = item

        source_hashes = []
        checks = {
            "recurring": False,
            "metered": True,
            "credits": True,
            "total": False,
            "usage_source_hash": False,
            "calculation_hash": False,
        }

        recurring = [
            line for line in invoice.lines
            if line.line_type == "RECURRING"
        ]
        checks["recurring"] = (
            len(recurring) == 1
            and recurring[0].amount_minor == plan.recurring_amount_minor
        )

        rates = {(r.metric, r.unit): r for r in plan.metered_rates}
        for line in invoice.lines:
            if line.line_type != "METERED":
                continue
            if not line.usage_aggregate_id:
                checks["metered"] = False
                break
            evidence = evidence_by_id.get(line.usage_aggregate_id)
            if evidence is None:
                checks["metered"] = False
                break
            if not self._same_tenant(evidence.tenant, invoice.tenant):
                checks["metered"] = False
                break
            rate = rates.get((evidence.metric, evidence.unit))
            if rate is None:
                checks["metered"] = False
                break
            billable = max(
                Decimal("0"),
                _decimal_quantity(evidence.total_quantity)
                - _decimal_quantity(rate.included_quantity),
            )
            expected = int(
                (billable * Decimal(rate.unit_price_minor)).quantize(
                    Decimal("1"),
                    rounding=ROUND_HALF_UP,
                )
            )
            if (
                expected != line.amount_minor
                or canonical_quantity(str(billable)) != line.quantity
                or rate.unit_price_minor != line.unit_price_minor
            ):
                checks["metered"] = False
                break
            source_hashes.append(evidence.source_hash)

        subtotal = sum(
            line.amount_minor
            for line in invoice.lines
            if line.line_type != "CREDIT"
        )
        credits = -sum(
            line.amount_minor
            for line in invoice.lines
            if line.line_type == "CREDIT"
        )

        for line in invoice.lines:
            if line.line_type != "CREDIT":
                continue
            credit = self._credits.get(str(line.credit_id))
            if (
                credit is None
                or credit.currency != invoice.currency
                or not self._same_tenant(credit.tenant, invoice.tenant)
                or -line.amount_minor > credit.amount_minor
            ):
                checks["credits"] = False
                break

        checks["total"] = (
            subtotal == invoice.subtotal_minor
            and credits == invoice.credit_minor
            and invoice.total_minor == subtotal - credits
            and invoice.total_minor >= 0
        )

        expected_source_hash = sha256(
            _canonical(sorted(source_hashes)).encode("utf-8")
        ).hexdigest()
        checks["usage_source_hash"] = (
            expected_source_hash == invoice.usage_source_hash
        )

        expected_manifest = self._calculation_manifest(
            subscription=subscription,
            plan=plan,
            lines=invoice.lines,
            usage_source_hash=invoice.usage_source_hash,
        )
        expected_calculation_hash = sha256(
            _canonical(expected_manifest).encode("utf-8")
        ).hexdigest()
        checks["calculation_hash"] = (
            expected_calculation_hash == invoice.calculation_hash
        )

        return {
            "valid": all(checks.values()),
            "checks": checks,
            "invoice_id": invoice.invoice_id,
        }

    def _require_plan(self, plan_id: str, version: int) -> PlanVersion:
        plan = self._plans.get((str(plan_id).strip(), version))
        if plan is None:
            raise BillingBaaSError("plan version not found")
        return plan

    def _get_subscription(
        self,
        subscription_id: str,
        request_context: Any,
    ) -> Subscription:
        self._validate_request_context(request_context)
        subscription = self._subscriptions.get(str(subscription_id).strip())
        if subscription is None:
            raise BillingBaaSError("subscription not found")
        tenant = self._tenant_from_context(request_context)
        if not self._same_tenant(subscription.tenant, tenant):
            raise BillingBaaSError("cross-tenant subscription access denied")
        return subscription

    def _get_invoice(
        self,
        invoice_id: str,
        request_context: Any,
    ) -> Invoice:
        self._validate_request_context(request_context)
        invoice = self._invoices.get(str(invoice_id).strip())
        if invoice is None:
            raise BillingBaaSError("invoice not found")
        tenant = self._tenant_from_context(request_context)
        if not self._same_tenant(invoice.tenant, tenant):
            raise BillingBaaSError("cross-tenant invoice access denied")
        return invoice

    @staticmethod
    def _line_id(*parts: str) -> str:
        return (
            "invoice_line_"
            + sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:24]
        )

    @staticmethod
    def _calculation_manifest(
        *,
        subscription: Subscription,
        plan: PlanVersion,
        lines: tuple[InvoiceLine, ...],
        usage_source_hash: str,
    ) -> dict[str, Any]:
        return {
            "subscription_id": subscription.subscription_id,
            "period_start": subscription.current_period_start,
            "period_end": subscription.current_period_end,
            "plan_id": plan.plan_id,
            "plan_version": plan.version,
            "currency": plan.currency,
            "usage_source_hash": usage_source_hash,
            "lines": [
                {
                    "line_id": line.line_id,
                    "line_type": line.line_type,
                    "amount_minor": line.amount_minor,
                    "metric": line.metric,
                    "unit": line.unit,
                    "quantity": line.quantity,
                    "unit_price_minor": line.unit_price_minor,
                    "usage_aggregate_id": line.usage_aggregate_id,
                    "credit_id": line.credit_id,
                }
                for line in lines
            ],
        }

    @staticmethod
    def _billing_event(
        event_type: str,
        resource_id: str,
        request_context: Any,
        occurred_at: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "event_type": event_type,
            "event_version": "1",
            "organization_id": request_context.organization_id,
            "workspace_id": request_context.workspace_id,
            "project_id": request_context.project_id,
            "environment_id": request_context.environment_id,
            "resource_type": "billing",
            "resource_id": resource_id,
            "occurred_at": occurred_at,
            "correlation_id": request_context.correlation_id,
            "actor_type": request_context.actor_type,
            "actor_id": request_context.actor_id,
            "payload": payload,
        }
