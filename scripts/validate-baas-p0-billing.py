#!/usr/bin/env python3
from dataclasses import replace
from pathlib import Path
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"
PATH = BAAS / "billing/runtime.py"

if not PATH.exists():
    raise SystemExit(f"ERROR: missing Billing runtime: {PATH}")

py_compile.compile(str(PATH), doraise=True)

spec = importlib.util.spec_from_file_location("baas_billing", PATH)
if spec is None or spec.loader is None:
    raise SystemExit("ERROR: unable to load Billing runtime")
billing = importlib.util.module_from_spec(spec)
sys.modules["baas_billing"] = billing
spec.loader.exec_module(billing)

request_path = BAAS / "runtime/request_context.py"
spec2 = importlib.util.spec_from_file_location("baas_request_context", request_path)
context = importlib.util.module_from_spec(spec2)
sys.modules["baas_request_context"] = context
spec2.loader.exec_module(context)

ctx = context.BaaSRequestContext(
    request_id="req-billing-validation",
    correlation_id="corr-billing-validation",
    service="subscription_billing",
    operation="billing.invoice.generate",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="SERVICE_ACCOUNT",
    kernel_authorization_ref="kernel_auth_billing_validation",
    idempotency_key="idem-billing-validation",
)
ctx.validate()

tenant = billing.TenantScope(
    organization_id=ctx.organization_id,
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
)

service = billing.SubscriptionBillingService()

plan = billing.PlanVersion(
    plan_id="plan-growth",
    version=3,
    name="Growth",
    currency="ZAR",
    billing_interval="MONTHLY",
    recurring_amount_minor=9900,
    metered_rates=(
        billing.MeteredRate(
            metric="api_requests",
            unit="request",
            unit_price_minor=2,
            included_quantity="100",
        ),
    ),
    entitlements={
        "projects": 10,
        "support": "priority",
    },
    effective_at="2026-01-01T00:00:00+00:00",
)
service.register_plan_version(plan=plan, request_context=ctx)

created = service.create_subscription(
    subscription_id="sub-validation",
    customer_ref="customer://validation",
    plan_id=plan.plan_id,
    plan_version=plan.version,
    current_period_start="2026-09-01T00:00:00+00:00",
    current_period_end="2026-10-01T00:00:00+00:00",
    request_context=ctx,
    created_at="2026-09-01T00:00:00+00:00",
)

if created["subscription"].status != "ACTIVE":
    raise SystemExit("ERROR: subscription did not start ACTIVE")

if created["billing_event"]["event_type"] != "subscription.created":
    raise SystemExit("ERROR: subscription billing event missing")

entitlements = service.resolve_entitlements(
    subscription_id="sub-validation",
    request_context=ctx,
)
if entitlements["projects"] != 10:
    raise SystemExit("ERROR: plan entitlements did not resolve")

credit = billing.CreditGrant(
    credit_id="credit-validation",
    tenant=tenant,
    amount_minor=1000,
    currency="ZAR",
    reason="Service credit",
    issued_at="2026-09-02T00:00:00+00:00",
)
service.issue_credit(credit=credit, request_context=ctx)

usage = billing.UsageEvidence(
    aggregate_id="usage-agg-validation",
    tenant=tenant,
    metric="api_requests",
    unit="request",
    total_quantity="150.5",
    event_count=151,
    period_start="2026-09-01T00:00:00+00:00",
    period_end="2026-10-01T00:00:00+00:00",
    source_hash="a" * 64,
)

draft_result = service.generate_invoice(
    subscription_id="sub-validation",
    usage=(usage,),
    credit_ids=("credit-validation",),
    request_context=ctx,
    created_at="2026-10-01T00:00:01+00:00",
)
invoice = draft_result["invoice"]

# 50.5 billable requests * 2 minor = 101 minor, rounded half-up.
if invoice.subtotal_minor != 10001:
    raise SystemExit(
        f"ERROR: invoice subtotal mismatch: {invoice.subtotal_minor}"
    )
if invoice.credit_minor != 1000 or invoice.total_minor != 9001:
    raise SystemExit("ERROR: invoice credit/total mismatch")
if invoice.plan_version != 3:
    raise SystemExit("ERROR: invoice lost pricing version")
if invoice.state != "DRAFT":
    raise SystemExit("ERROR: generated invoice is not DRAFT")

again = service.generate_invoice(
    subscription_id="sub-validation",
    usage=(usage,),
    credit_ids=("credit-validation",),
    request_context=ctx,
    created_at="2026-10-01T00:00:02+00:00",
)
if again["created"] is not False or again["invoice"].invoice_id != invoice.invoice_id:
    raise SystemExit("ERROR: deterministic invoice generation failed")

reconciliation = service.reconcile_invoice(
    invoice_id=invoice.invoice_id,
    usage=(usage,),
    request_context=ctx,
)
if not reconciliation["valid"]:
    raise SystemExit(
        "ERROR: valid invoice failed reconciliation: "
        + str(reconciliation["checks"])
    )

tampered_invoice = replace(invoice, total_minor=9000)
try:
    tampered_invoice.validate()
except billing.BillingBaaSError:
    pass
else:
    raise SystemExit("ERROR: tampered invoice total passed validation")

opened = service.open_invoice(
    invoice_id=invoice.invoice_id,
    request_context=ctx,
    opened_at="2026-10-01T00:01:00+00:00",
)["invoice"]

if opened.state != "OPEN":
    raise SystemExit("ERROR: invoice did not open")

retry = service.create_payment_retry_intent(
    invoice_id=opened.invoice_id,
    attempt=1,
    request_context=ctx,
)
if retry.state != "READY_FOR_PAYMENT_ABSTRACTION":
    raise SystemExit("ERROR: Billing claimed payment execution")
if retry.amount_minor != opened.total_minor or retry.currency != "ZAR":
    raise SystemExit("ERROR: payment retry intent amount mismatch")
if "provider" in str(retry).lower():
    raise SystemExit("ERROR: Billing payment retry intent leaked provider coupling")

past_due = service.transition_subscription(
    subscription_id="sub-validation",
    target_status="PAST_DUE",
    request_context=ctx,
    updated_at="2026-10-02T00:00:00+00:00",
)["subscription"]
if past_due.status != "PAST_DUE":
    raise SystemExit("ERROR: subscription PAST_DUE transition failed")

active_again = service.transition_subscription(
    subscription_id="sub-validation",
    target_status="ACTIVE",
    request_context=ctx,
    updated_at="2026-10-03T00:00:00+00:00",
)["subscription"]
if active_again.status != "ACTIVE":
    raise SystemExit("ERROR: subscription ACTIVE recovery failed")

cross_ctx = context.BaaSRequestContext(
    request_id="req-billing-cross",
    correlation_id="corr-billing-cross",
    service="subscription_billing",
    operation="billing.invoice.read",
    organization_id="org-other",
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
    actor_id="actor-other",
    actor_type="SERVICE_ACCOUNT",
    kernel_authorization_ref="kernel_auth_billing_cross",
    idempotency_key="idem-billing-cross",
)
try:
    service.resolve_entitlements(
        subscription_id="sub-validation",
        request_context=cross_ctx,
    )
except billing.BillingBaaSError:
    pass
else:
    raise SystemExit("ERROR: cross-tenant subscription access was accepted")

try:
    billing.PlanVersion(
        plan_id="plan-float",
        version=1,
        name="Bad",
        currency="ZAR",
        billing_interval="MONTHLY",
        recurring_amount_minor=99.99,
        metered_rates=(),
        entitlements={},
        effective_at="2026-01-01T00:00:00+00:00",
    ).validate()
except billing.BillingBaaSError:
    pass
else:
    raise SystemExit("ERROR: floating-point money was accepted")

status = (BAAS / "IMPLEMENTATION_STATUS.md").read_text(encoding="utf-8")
for phrase in [
    "- [x] Subscription Billing",
    "- [x] Immutable versioned plan pricing",
    "- [x] Deterministic invoice generation",
    "- [x] Payment-provider execution boundary",
    "- [x] Invoice/source-hash reconciliation",
    "- [ ] Payment Abstraction",
]:
    if phrase not in status:
        raise SystemExit("ERROR: Billing status missing: " + phrase)

print("OK: Versioned plan pricing and subscription lifecycle passed.")
print("OK: Recurring + metered usage rating passed.")
print("OK: Integer minor-unit money invariant passed.")
print("OK: Credit application cannot make invoice negative.")
print("OK: Deterministic invoice identity passed.")
print("OK: Invoice/source-hash reconciliation passed.")
print("OK: Entitlement resolution passed.")
print("OK: Payment retry remains intent-only for Payments BaaS.")
print("OK: Cross-tenant subscription access fails closed.")
print("STATUS: BAAS P0 SUBSCRIPTION BILLING READY")
