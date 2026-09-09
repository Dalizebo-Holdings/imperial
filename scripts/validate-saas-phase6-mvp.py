#!/usr/bin/env python3
from pathlib import Path
import importlib
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
SAAS = ROOT / "saas"
KERNEL = ROOT / "kernel"
BAAS = ROOT / "baas"

root_text = str(ROOT)
if root_text not in sys.path:
    sys.path.insert(0, root_text)

required_files = [
    SAAS / "MVP_ACCEPTANCE.md",
    SAAS / "PHASE6_MVP_ACCEPTANCE.md",
    SAAS / "STATUS.md",
    SAAS / "IMPLEMENTATION_STATUS.md",
    SAAS / "COMMERCE_POS_FOUNDATION.md",
    SAAS / "runtime/product_context.py",
    SAAS / "commerce/store/STORE_CONTRACT.md",
    SAAS / "commerce/catalogue/runtime.py",
    SAAS / "commerce/inventory/runtime.py",
    SAAS / "commerce/customers/runtime.py",
    SAAS / "commerce/checkout/runtime.py",
    SAAS / "commerce/operations/runtime.py",
    SAAS / "commerce/refunds/runtime.py",
    SAAS / "pos/foundation/runtime.py",
    SAAS / "pos/transactions/runtime.py",
    SAAS / "pos/returns/runtime.py",
    KERNEL / "STATUS.md",
    KERNEL / "commerce/runtime.py",
    BAAS / "STATUS.md",
    BAAS / "payments/runtime.py",
    BAAS / "runtime/request_context.py",
]

for path in required_files:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Phase 6 acceptance prerequisite: {path}"
        )

python_files = [
    SAAS / "runtime/product_context.py",
    SAAS / "commerce/catalogue/runtime.py",
    SAAS / "commerce/inventory/runtime.py",
    SAAS / "commerce/customers/runtime.py",
    SAAS / "commerce/checkout/runtime.py",
    SAAS / "commerce/operations/runtime.py",
    SAAS / "commerce/refunds/runtime.py",
    SAAS / "pos/foundation/runtime.py",
    SAAS / "pos/transactions/runtime.py",
    SAAS / "pos/returns/runtime.py",
    KERNEL / "commerce/runtime.py",
    BAAS / "payments/runtime.py",
    BAAS / "runtime/request_context.py",
]

for path in python_files:
    py_compile.compile(
        str(path),
        doraise=True,
    )

mvp = (SAAS / "MVP_ACCEPTANCE.md").read_text(
    encoding="utf-8"
)

for phrase in [
    "Store can be configured",
    "Products can be created",
    "Inventory can be maintained",
    "Customers can checkout",
    "Orders reach correct final state",
    "Payments reconcile",
    "Refunds are auditable",
    "Staff can authenticate",
    "Products can be searched",
    "Sales can be completed",
    "Inventory is deducted correctly",
    "Returns are recorded correctly",
    "Receipts can be issued",
    "Branch reports are available",
    "No cross-tenant exposure",
    "No duplicated authoritative business models",
    "Critical operations are idempotent",
    "Audit events exist",
    "Logs and metrics are available",
    "Backup restore has been tested",
]:
    if phrase not in mvp:
        raise SystemExit(
            "ERROR: formal MVP criterion missing: " + phrase
        )

kernel_status = (KERNEL / "STATUS.md").read_text(
    encoding="utf-8"
)
for phrase in [
    "Kernel P0 complete.",
    "Structured logging: COMPLETE",
    "Metrics contract: COMPLETE",
    "Backup contract: COMPLETE",
    "Shared commerce primitives: COMPLETE",
]:
    if phrase not in kernel_status:
        raise SystemExit(
            "ERROR: Kernel acceptance evidence missing: " + phrase
        )

baas_status = (BAAS / "STATUS.md").read_text(
    encoding="utf-8"
)
for phrase in [
    "Dalizebo BaaS P0 complete.",
    "Authentication: COMPLETE",
    "Audit: COMPLETE",
    "Logging: COMPLETE",
    "Usage Metering: COMPLETE",
    "Payment Abstraction: COMPLETE",
    "Backups: COMPLETE",
    "Restore testing: COMPLETE",
    "Trusted recovery gate: COMPLETE",
]:
    if phrase not in baas_status:
        raise SystemExit(
            "ERROR: BaaS acceptance evidence missing: " + phrase
        )

implementation = (
    SAAS / "IMPLEMENTATION_STATUS.md"
).read_text(encoding="utf-8")

for phrase in [
    "DALIZEBO COMMERCE P0: COMPLETE",
    "DALIZEBO POS P0: COMPLETE",
    "- [x] Store setup",
    "- [x] Product catalogue",
    "- [x] Inventory",
    "- [x] Customers",
    "- [x] Checkout",
    "- [x] Orders",
    "- [x] Payments",
    "- [x] Branches",
    "- [x] Staff",
    "- [x] Product search",
    "- [x] Inventory deduction",
    "- [x] Returns",
    "- [x] Daily summaries",
]:
    if phrase not in implementation:
        raise SystemExit(
            "ERROR: Phase 6 implementation evidence missing: " + phrase
        )

# SaaS owns orchestration/projection state, not authoritative SQL schemas.
saas_sql = [
    path
    for path in SAAS.rglob("*.sql")
    if path.is_file()
]
if saas_sql:
    raise SystemExit(
        "ERROR: SaaS authoritative SQL files detected: "
        + ", ".join(str(path.relative_to(ROOT)) for path in saas_sql)
    )


def load(name):
    try:
        return importlib.import_module(name)
    except Exception as exc:
        raise SystemExit(
            f"ERROR: unable to import {name}: {exc}"
        ) from exc


foundation = load("saas.runtime.product_context")
refunds = load("saas.commerce.refunds.runtime")
kernel = load("kernel.commerce.runtime")
payments = load("baas.payments.runtime")
baas_context = load("baas.runtime.request_context")

# Shared authority/idempotency/audit gate.
commerce_context = foundation.ProductContext(
    product="COMMERCE",
    organization_id="org-phase6",
    workspace_id="workspace-phase6",
    project_id="project-phase6",
    environment_id="env-phase6",
    actor_id="actor-phase6",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_phase6_acceptance",
    correlation_id="corr-phase6-acceptance",
    store_id="store-phase6",
)

foundation_service = foundation.CommercePOSFoundation()

probe = foundation.ProductCommand(
    action="CREATE",
    entity_type="REFUND",
    entity_id="refund-authority-probe",
    context=commerce_context,
    idempotency_key="refund-authority-probe",
    input_metadata={
        "payment_id": "payment-authority-probe",
        "amount_minor": 100,
        "currency": "ZAR",
    },
)

first = foundation_service.plan(probe)
second = foundation_service.plan(probe)

if (
    first["plan"].authority != "kernel.commerce"
    or first["plan"].baas_service != "baas.payment_abstraction"
):
    raise SystemExit(
        "ERROR: REFUND authority route bypasses Kernel/BaaS"
    )

if (
    second["created"] is not False
    or second["plan"].command_id != first["plan"].command_id
):
    raise SystemExit(
        "ERROR: shared critical-operation idempotency failed"
    )

if (
    first["plan"].audit_event.get("event_type")
    != "saas.product_command.planned"
):
    raise SystemExit(
        "ERROR: shared ProductCommand audit evidence missing"
    )

try:
    foundation_service.plan(
        foundation.ProductCommand(
            action="CREATE",
            entity_type="REFUND",
            entity_id="refund-authority-probe",
            context=commerce_context,
            idempotency_key="refund-authority-probe",
            input_metadata={
                "payment_id": "payment-authority-probe",
                "amount_minor": 101,
                "currency": "ZAR",
            },
        )
    )
except Exception:
    pass
else:
    raise SystemExit(
        "ERROR: idempotency key conflict did not fail closed"
    )


def kernel_transition_validator(
    current,
    target,
    payment_id,
    order_id,
    amount_minor,
    currency,
):
    try:
        kernel.PaymentState(
            payment_id=payment_id,
            order_id=order_id,
            status=current,
            amount=kernel.Money(
                amount_minor=amount_minor,
                currency=currency,
            ),
        ).transition(target)
        return True
    except Exception:
        return False


def kernel_refund_validator(
    payment_id,
    amount_minor,
    currency,
    captured_amount_minor,
    previously_refunded_minor,
    reason,
):
    try:
        kernel.Refund(
            refund_id="phase6-kernel-refund-probe",
            payment_id=payment_id,
            amount=kernel.Money(
                amount_minor=amount_minor,
                currency=currency,
            ),
            reason=reason,
        ).validate(
            captured_amount=kernel.Money(
                amount_minor=captured_amount_minor,
                currency=currency,
            ),
            previously_refunded_minor=previously_refunded_minor,
        )
        return True
    except Exception:
        return False


payment_service = payments.PaymentAbstractionService(
    kernel_transition_validator=kernel_transition_validator,
    kernel_refund_validator=kernel_refund_validator,
)

provider_context = baas_context.BaaSRequestContext(
    request_id="req-phase6-provider",
    correlation_id=commerce_context.correlation_id,
    service="payments",
    operation="provider.register",
    organization_id=commerce_context.organization_id,
    workspace_id=commerce_context.workspace_id,
    project_id=commerce_context.project_id,
    environment_id=commerce_context.environment_id,
    actor_id=commerce_context.actor_id,
    actor_type=commerce_context.actor_type,
    kernel_authorization_ref=commerce_context.kernel_authorization_ref,
    idempotency_key="phase6-provider-register",
)

payment_service.register_provider(
    provider=payments.ProviderConfiguration(
        provider_id="phase6_provider",
        adapter_ref="adapter://payments/phase6",
        credential_ref="vault://payments/phase6/control",
        supported_currencies=("ZAR",),
        capabilities=("AUTHORIZE", "CAPTURE", "REFUND"),
    ),
    request_context=provider_context,
)

payment_request = payments.PaymentRequest(
    payment_request_id="phase6-payment-request",
    source_type="ORDER",
    source_ref="order-phase6",
    amount_minor=5000,
    currency="ZAR",
    capture_mode="AUTHORIZE_CAPTURE",
    idempotency_key="phase6-payment",
    requested_at="2026-09-09T18:00:00+00:00",
)

payment_plan = payment_service.create_payment_plan(
    provider_id="phase6_provider",
    request=payment_request,
    request_context=provider_context,
)["plan"]

payment_service.plan_provider_result(
    result=payments.ProviderResult(
        payment_id=payment_plan.payment_id,
        provider_id="phase6_provider",
        provider_reference="phase6-provider-payment-ref",
        outcome="CAPTURED",
        amount_minor=5000,
        currency="ZAR",
        occurred_at="2026-09-09T18:00:01+00:00",
    ),
    kernel_current_status="PENDING",
    request_context=provider_context,
)

reconciliation = payment_service.reconcile(
    payment_id=payment_plan.payment_id,
    kernel_status="CAPTURED",
    kernel_amount_minor=5000,
    kernel_currency="ZAR",
    kernel_provider_reference="phase6-provider-payment-ref",
    provider_status="CAPTURED",
    provider_amount_minor=5000,
    provider_currency="ZAR",
    provider_reference="phase6-provider-payment-ref",
    request_context=provider_context,
)

if reconciliation.state != "MATCH":
    raise SystemExit(
        "ERROR: Payment Abstraction reconciliation acceptance failed"
    )

refund_service = refunds.CommerceRefundService(
    foundation=foundation_service,
    product_command_type=foundation.ProductCommand,
    kernel_money_type=kernel.Money,
    kernel_refund_type=kernel.Refund,
    kernel_payment_state_type=kernel.PaymentState,
    kernel_currency_validator=kernel.validate_currency,
    baas_payment_service=payment_service,
    baas_refund_request_type=payments.RefundRequest,
    baas_request_context_type=baas_context.BaaSRequestContext,
)


def evidence(entity_type, entity_id, status, org="org-phase6"):
    return refunds.CommerceRefundEvidence(
        source="kernel.commerce",
        entity_type=entity_type,
        entity_id=entity_id,
        organization_id=org,
        workspace_id=commerce_context.workspace_id,
        project_id=commerce_context.project_id,
        environment_id=commerce_context.environment_id,
        status=status,
    )


order_evidence = evidence(
    "ORDER",
    "order-phase6",
    "COMPLETED",
)
payment_evidence = evidence(
    "PAYMENT",
    payment_plan.payment_id,
    "CAPTURED",
)

partial_request = refunds.CommerceRefundRequest(
    refund_id="refund-phase6-partial",
    order_id="order-phase6",
    payment_id=payment_plan.payment_id,
    amount_minor=2500,
    captured_amount_minor=5000,
    previously_refunded_minor=0,
    currency="ZAR",
    reason="Phase 6 Commerce refund acceptance",
    provider_id="phase6_provider",
    provider_reference="phase6-provider-payment-ref",
    idempotency_key="phase6-refund-partial",
    requested_at="2026-09-09T18:01:00+00:00",
)

partial_plan = refund_service.plan_provider_refund(
    context=commerce_context,
    request=partial_request,
    order_evidence=order_evidence,
    payment_evidence=payment_evidence,
)

if (
    partial_plan.provider_operation_plan.state
    != "READY_FOR_PROVIDER_REFUND_ADAPTER"
):
    raise SystemExit(
        "ERROR: Commerce refund bypassed provider abstraction boundary"
    )

if hasattr(
    partial_plan.provider_operation_plan,
    "credential_value",
):
    raise SystemExit(
        "ERROR: Commerce refund exposes provider credential value"
    )

partial_completion = refunds.ProviderRefundCompletion(
    result_ref="payment-refund-result://phase6/partial",
    refund_id=partial_request.refund_id,
    payment_id=partial_request.payment_id,
    provider_id=partial_request.provider_id,
    provider_reference=partial_request.provider_reference,
    amount_minor=partial_request.amount_minor,
    currency="ZAR",
    outcome="SUCCEEDED",
    completed_at="2026-09-09T18:01:01+00:00",
)

partial = refund_service.complete_provider_refund(
    context=commerce_context,
    request=partial_request,
    approved_plan=partial_plan,
    completion=partial_completion,
    order_evidence=order_evidence,
    payment_evidence=payment_evidence,
)

if partial.refund_create.entity_type != "REFUND":
    raise SystemExit(
        "ERROR: Commerce refund did not create shared REFUND command"
    )

if partial.payment_transition is not None:
    raise SystemExit(
        "ERROR: partial Commerce refund incorrectly finalized Payment"
    )

if not partial.refund_create.audit_event:
    raise SystemExit(
        "ERROR: Commerce Refund command is not auditable"
    )

full_request = refunds.CommerceRefundRequest(
    refund_id="refund-phase6-final",
    order_id="order-phase6",
    payment_id=payment_plan.payment_id,
    amount_minor=2500,
    captured_amount_minor=5000,
    previously_refunded_minor=2500,
    currency="ZAR",
    reason="Final Phase 6 Commerce refund acceptance",
    provider_id="phase6_provider",
    provider_reference="phase6-provider-payment-ref",
    idempotency_key="phase6-refund-final",
    requested_at="2026-09-09T18:02:00+00:00",
)

full_plan = refund_service.plan_provider_refund(
    context=commerce_context,
    request=full_request,
    order_evidence=order_evidence,
    payment_evidence=payment_evidence,
)

full = refund_service.complete_provider_refund(
    context=commerce_context,
    request=full_request,
    approved_plan=full_plan,
    completion=refunds.ProviderRefundCompletion(
        result_ref="payment-refund-result://phase6/final",
        refund_id=full_request.refund_id,
        payment_id=full_request.payment_id,
        provider_id=full_request.provider_id,
        provider_reference=full_request.provider_reference,
        amount_minor=full_request.amount_minor,
        currency="ZAR",
        outcome="SUCCEEDED",
        completed_at="2026-09-09T18:02:01+00:00",
    ),
    order_evidence=order_evidence,
    payment_evidence=payment_evidence,
)

if (
    full.payment_transition is None
    or full.payment_transition.input_metadata["to_status"]
    != "REFUNDED"
):
    raise SystemExit(
        "ERROR: full Commerce refund did not explicitly transition Payment"
    )

try:
    refund_service.plan_provider_refund(
        context=commerce_context,
        request=partial_request,
        order_evidence=evidence(
            "ORDER",
            "order-phase6",
            "COMPLETED",
            org="org-other",
        ),
        payment_evidence=payment_evidence,
    )
except refunds.CommerceRefundError:
    pass
else:
    raise SystemExit(
        "ERROR: cross-tenant Commerce refund evidence was accepted"
    )

# POS and Commerce completion evidence remains required after the runtime smoke.
saas_status = (SAAS / "STATUS.md").read_text(
    encoding="utf-8"
)
if (
    "DALIZEBO POS P0: COMPLETE" not in saas_status
    and "POS P0: COMPLETE" not in saas_status
):
    raise SystemExit(
        "ERROR: POS P0 completion evidence missing"
    )

if (
    "Dalizebo Commerce P0: COMPLETE" not in saas_status
    and "Commerce P0: COMPLETE" not in saas_status
):
    raise SystemExit(
        "ERROR: Commerce P0 completion evidence missing"
    )

print("OK: Formal Commerce/POS/Platform MVP criteria are present.")
print("OK: Kernel/BaaS P0 platform prerequisites remain complete.")
print("OK: SaaS contains no authoritative SQL schema.")
print("OK: Shared REFUND authority/idempotency/audit routing passed.")
print("OK: BaaS Payment reconciliation passed.")
print("OK: Commerce provider refund planning passed.")
print("OK: Commerce partial/full refund state invariants passed.")
print("OK: Cross-tenant Commerce refund evidence fails closed.")
print("OK: POS and Commerce P0 completion evidence is present.")
print("STATUS: PHASE 6 COMMERCE + POS MVP ACCEPTANCE READY")
