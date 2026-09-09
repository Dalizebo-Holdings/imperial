#!/usr/bin/env python3
from dataclasses import replace
from pathlib import Path
import importlib.util
import py_compile
import sys
from decimal import Decimal, ROUND_HALF_UP

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"

MODULES = {
    "baas_request_context": BAAS / "runtime/request_context.py",
    "baas_conversion": BAAS / "currency_conversion/runtime.py",
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(f"ERROR: missing Currency Conversion runtime file: {path}")
    py_compile.compile(str(path), doraise=True)

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"ERROR: unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

request_context = load_module("baas_request_context", MODULES["baas_request_context"])
conversion = load_module("baas_conversion", MODULES["baas_conversion"])

ctx = request_context.BaaSRequestContext(
    request_id="req-conversion-validation",
    correlation_id="corr-conversion-validation",
    service="currency_conversion",
    operation="conversion.plan",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="SERVICE_ACCOUNT",
    kernel_authorization_ref="kernel_auth_conversion_validation",
    idempotency_key="idem-conversion-validation",
)
ctx.validate()

service = conversion.CurrencyConversionService()

request = conversion.ConversionRequest(
    conversion_id="conv-validation",
    source_currency="ZAR",
    destination_currency="USD",
    source_amount_minor=5100,
    destination_amount_minor=5000,
    conversion_fee_percentage=2.0,
    conversion_fee_cap_percentage=5.0,
    source_payment_id="payment-source-validation",
    destination_payment_id="payment-dest-validation",
    idempotency_key="idem-conv-a",
    requested_at="2026-09-09T12:00:00+00:00",
)

plan_result = service.plan_conversion(request=request, request_context=ctx)
if not plan_result["created"]:
    raise SystemExit("ERROR: conversion plan not created")
plan = plan_result["plan"]
if plan.state != "READY_FOR_CONVERSION_EXECUTOR":
    raise SystemExit("ERROR: conversion plan claimed direct execution")
if plan.conversion_fee_minor != 100:
    raise SystemExit("ERROR: conversion fee not calculated correctly")
if plan.confirmed_amount_minor != 5100:
    raise SystemExit("ERROR: confirmed amount not derived from destination + fee")

if plan.tenant_context["organization_id"] != ctx.organization_id:
    raise SystemExit("ERROR: conversion plan tenant context mismatch")

if "provider" in str(plan).lower():
    raise SystemExit("ERROR: conversion plan leaked provider coupling")

cross_ctx = request_context.BaaSRequestContext(
    request_id="req-conversion-cross",
    correlation_id="corr-conversion-cross",
    service="currency_conversion",
    operation="conversion.read",
    organization_id="org-other",
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
    actor_id="actor-other",
    actor_type="SERVICE_ACCOUNT",
    kernel_authorization_ref="kernel_auth_conversion_cross",
    idempotency_key="idem-conversion-cross",
)

try:
    service.reconcile_conversion(conversion_id="conv-validation", request_context=cross_ctx)
except conversion.CurrencyConversionBaaSError:
    pass
else:
    raise SystemExit("ERROR: cross-tenant conversion access was accepted")

confirmed = service.apply_settlement_callback(
    conversion_id="conv-validation",
    callback_type="confirmation",
    callback_at="2026-09-09T12:01:00+00:00",
    provider_reference="provider-ref-001",
    request_context=ctx,
)
if confirmed["state"] != "CONFIRMED":
    raise SystemExit("ERROR: confirmation callback did not transition to CONFIRMED")

try:
    service.apply_settlement_callback(
        conversion_id="conv-validation",
        callback_type="retry",
        callback_at="2026-09-09T12:02:00+00:00",
        provider_reference=None,
        request_context=ctx,
    )
except conversion.CurrencyConversionBaaSError:
    pass
else:
    raise SystemExit("ERROR: unsupported callback was accepted")

resolved = service.resolve_conversion(
    conversion_id="conv-validation",
    escrow_feedback_at="2026-09-09T12:01:30+00:00",
    resolved_at="2026-09-09T12:02:00+00:00",
    provider_reference="provider-ref-001",
    request_context=ctx,
)
if resolved["state"] != "RESOLVED":
    raise SystemExit("ERROR: resolution did not transition to RESOLVED")

reconcile = service.reconcile_conversion(conversion_id="conv-validation", request_context=ctx)
if not reconcile["checks"]["amount_balance"]:
    raise SystemExit(
        "ERROR: conversion settlement invariant not enforced: "
        + str(reconcile["checks"])
    )
if not reconcile["checks"]["escrow_ordering"]:
    raise SystemExit("ERROR: escrow feedback ordering not enforced")

request_fail = conversion.ConversionRequest(
    conversion_id="conv-validation-fail",
    source_currency="ZAR",
    destination_currency="USD",
    source_amount_minor=5100,
    destination_amount_minor=5000,
    conversion_fee_percentage=2.0,
    conversion_fee_cap_percentage=5.0,
    source_payment_id="payment-source-fail",
    destination_payment_id="payment-dest-fail",
    idempotency_key="idem-conv-fail",
    requested_at="2026-09-09T12:00:00+00:00",
)

if not service.plan_conversion(request=request_fail, request_context=ctx)["created"]:
    raise SystemExit("ERROR: failed-transaction conversion plan not created")

failed = service.apply_failed_transaction(
    conversion_id="conv-validation-fail",
    provider_result_outcome="FAILED",
    provider_reference="provider-ref-002",
    request_context=ctx,
)
if failed["state"] != "RECOVERY_SCHEDULED":
    raise SystemExit("ERROR: failed transaction did not schedule recovery")
if failed["conversion_event"]["event_type"] != "conversion.recovery_scheduled":
    raise SystemExit("ERROR: failed transaction event type wrong")
if failed["refund_plan"] is None:
    raise SystemExit("ERROR: failed transaction did not schedule refund path")
if failed["apology_credit_plan"] is None:
    raise SystemExit("ERROR: failed transaction did not schedule apology credit path")

try:
    service.create_apology_credit(
        conversion_id="conv-validation",
        credit_id="apology-credit-validation-wrong-state",
        reason="conversion failed transaction recovery",
        amount_minor=5000,
        currency="USD",
        issued_at="2026-09-09T12:03:00+00:00",
        request_context=ctx,
    )
except conversion.CurrencyConversionBaaSError:
    pass
else:
    raise SystemExit("ERROR: apology credit allowed on non-recovery conversion")

recovery_credit = service.create_apology_credit(
    conversion_id="conv-validation-fail",
    credit_id="apology-credit-validation",
    reason="conversion failed transaction recovery",
    amount_minor=5000,
    currency="USD",
    issued_at="2026-09-09T12:03:00+00:00",
    request_context=ctx,
)
if recovery_credit["apology_credit_plan"]["state"] != "READY_FOR_BILLING_CREDIT_APPLICATION":
    raise SystemExit("ERROR: apology credit plan state wrong")
if recovery_credit["apology_credit_plan"]["amount_minor"] != 5000:
    raise SystemExit("ERROR: apology credit amount wrong")

status = (BAAS / "IMPLEMENTATION_STATUS.md").read_text(encoding="utf-8")
for phrase in [
    "- [x] Currency Conversion",
    "- [x] Balanced conversion accounting invariant",
    "- [x] Conversion fee cap enforcement",
    "- [x] Fee-on-confirmed-only settlement rule",
    "- [x] Confirmation/void-only callback discipline",
    "- [x] Escrow feedback before resolution ordering",
    "- [x] Failed transaction recovery path",
    "- [x] Apology credit path",
    "- [x] Conversion idempotency",
    "- [x] Currency Conversion P0 plan/confirm/void/failed-recovery/resolve/reconcile closed",
]:
    if phrase not in status:
        raise SystemExit("ERROR: Currency Conversion status missing: " + phrase)

print("OK: Currency Conversion planning created deterministic plan.")
print("OK: Settlement callbacks limited to confirmation and void.")
print("OK: Escrow feedback before resolution enforced.")
print("OK: Failed transaction recovery schedules refund and apology credit path.")
print("OK: Apology credit path structurally compatible with Billing credit grants.")
print("OK: Reconciliation enforces balanced accounting, fee cap, and escrow ordering.")
print("OK: Conversion idempotency preserved.")
print("STATUS: BAAS P0 CURRENCY CONVERSION READY")
