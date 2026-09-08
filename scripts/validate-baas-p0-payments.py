#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"
KERNEL = ROOT / "kernel"

MODULES = {
    "baas_request_context": BAAS / "runtime/request_context.py",
    "baas_payments": BAAS / "payments/runtime.py",
    "kernel_commerce": KERNEL / "commerce/runtime.py",
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Payment Abstraction runtime file: {path}"
        )
    py_compile.compile(str(path), doraise=True)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"ERROR: unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


request_context = load_module(
    "baas_request_context",
    MODULES["baas_request_context"],
)
payments = load_module(
    "baas_payments",
    MODULES["baas_payments"],
)
commerce = load_module(
    "kernel_commerce",
    MODULES["kernel_commerce"],
)


def kernel_transition_validator(
    current,
    target,
    payment_id,
    source_ref,
    amount_minor,
    currency,
):
    try:
        state = commerce.PaymentState(
            payment_id=payment_id,
            order_id=source_ref,
            status=current,
            amount=commerce.Money(
                amount_minor=amount_minor,
                currency=currency,
            ),
        )
        state.transition(target)
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
        refund = commerce.Refund(
            refund_id="refund-validation",
            payment_id=payment_id,
            amount=commerce.Money(
                amount_minor=amount_minor,
                currency=currency,
            ),
            reason=reason,
        )
        refund.validate(
            captured_amount=commerce.Money(
                amount_minor=captured_amount_minor,
                currency=currency,
            ),
            previously_refunded_minor=previously_refunded_minor,
        )
        return True
    except Exception:
        return False


ctx = request_context.BaaSRequestContext(
    request_id="req-payments-validation",
    correlation_id="corr-payments-validation",
    service="payments",
    operation="payment.plan",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="SERVICE_ACCOUNT",
    kernel_authorization_ref="kernel_auth_payments_validation",
    idempotency_key="idem-payments-validation",
)
ctx.validate()

service = payments.PaymentAbstractionService(
    kernel_transition_validator=kernel_transition_validator,
    kernel_refund_validator=kernel_refund_validator,
)

provider = payments.ProviderConfiguration(
    provider_id="provider_validation",
    adapter_ref="adapter://payments/provider-validation",
    credential_ref="vault://payments/provider-validation/api",
    supported_currencies=("ZAR", "USD"),
    capabilities=("AUTHORIZE", "CAPTURE", "REFUND"),
)
service.register_provider(
    provider=provider,
    request_context=ctx,
)

request = payments.PaymentRequest(
    payment_request_id="payreq-001",
    source_type="ORDER",
    source_ref="order-validation",
    amount_minor=10000,
    currency="ZAR",
    capture_mode="AUTHORIZE_CAPTURE",
    idempotency_key="order-validation-payment-1",
    requested_at="2026-09-08T21:00:00+00:00",
)

created = service.create_payment_plan(
    provider_id=provider.provider_id,
    request=request,
    request_context=ctx,
)

if created["created"] is not True:
    raise SystemExit("ERROR: first payment plan was not created")

plan = created["plan"]

if plan.state != "READY_FOR_PROVIDER_ADAPTER":
    raise SystemExit("ERROR: P0 Payments claimed provider execution")

if not plan.provider_credential_ref.startswith("vault://"):
    raise SystemExit("ERROR: provider credential reference was lost")

if hasattr(plan, "credential"):
    raise SystemExit("ERROR: raw provider credential field exists")

duplicate = service.create_payment_plan(
    provider_id=provider.provider_id,
    request=request,
    request_context=ctx,
)

if (
    duplicate["created"] is not False
    or duplicate["plan"].payment_id != plan.payment_id
):
    raise SystemExit("ERROR: idempotent payment planning failed")

try:
    service.create_payment_plan(
        provider_id=provider.provider_id,
        request=payments.PaymentRequest(
            payment_request_id="payreq-conflict",
            source_type="ORDER",
            source_ref="order-validation",
            amount_minor=20000,
            currency="ZAR",
            capture_mode="AUTHORIZE_CAPTURE",
            idempotency_key="order-validation-payment-1",
            requested_at="2026-09-08T21:00:00+00:00",
        ),
        request_context=ctx,
    )
except payments.PaymentsBaaSError:
    pass
else:
    raise SystemExit("ERROR: payment idempotency conflict was accepted")

result = payments.ProviderResult(
    payment_id=plan.payment_id,
    provider_id=provider.provider_id,
    provider_reference="provider-ref-001",
    outcome="CAPTURED",
    amount_minor=10000,
    currency="ZAR",
    occurred_at="2026-09-08T21:00:05+00:00",
)

transition = service.plan_provider_result(
    result=result,
    kernel_current_status="PENDING",
    request_context=ctx,
)

if transition.transition_sequence != ("AUTHORIZED", "CAPTURED"):
    raise SystemExit(
        "ERROR: immediate capture did not preserve explicit Kernel transitions"
    )

if transition.state != "READY_FOR_KERNEL_TRANSACTION_ADAPTER":
    raise SystemExit("ERROR: provider result claimed direct Kernel mutation")

refund = payments.RefundRequest(
    refund_id="refund-validation",
    payment_id=plan.payment_id,
    amount_minor=2500,
    currency="ZAR",
    reason="Customer return",
    idempotency_key="refund-validation-1",
    requested_at="2026-09-08T21:01:00+00:00",
)

refund_result = service.create_refund_plan(
    provider_id=provider.provider_id,
    provider_reference="provider-ref-001",
    request=refund,
    kernel_current_status="CAPTURED",
    captured_amount_minor=10000,
    previously_refunded_minor=1000,
    request_context=ctx,
)

if refund_result["plan"].state != "READY_FOR_PROVIDER_REFUND_ADAPTER":
    raise SystemExit("ERROR: refund plan claimed provider execution")

try:
    service.create_refund_plan(
        provider_id=provider.provider_id,
        provider_reference="provider-ref-001",
        request=payments.RefundRequest(
            refund_id="refund-too-large",
            payment_id=plan.payment_id,
            amount_minor=9500,
            currency="ZAR",
            reason="Invalid excessive refund",
            idempotency_key="refund-too-large",
            requested_at="2026-09-08T21:02:00+00:00",
        ),
        kernel_current_status="CAPTURED",
        captured_amount_minor=10000,
        previously_refunded_minor=1000,
        request_context=ctx,
    )
except payments.PaymentsBaaSError:
    pass
else:
    raise SystemExit("ERROR: refund exceeded captured amount")

matched = service.reconcile(
    payment_id=plan.payment_id,
    kernel_status="CAPTURED",
    kernel_amount_minor=10000,
    kernel_currency="ZAR",
    kernel_provider_reference="provider-ref-001",
    provider_status="CAPTURED",
    provider_amount_minor=10000,
    provider_currency="ZAR",
    provider_reference="provider-ref-001",
    request_context=ctx,
)

if matched.state != "MATCH":
    raise SystemExit("ERROR: matching payment failed reconciliation")

mismatch = service.reconcile(
    payment_id=plan.payment_id,
    kernel_status="CAPTURED",
    kernel_amount_minor=10000,
    kernel_currency="ZAR",
    kernel_provider_reference="provider-ref-001",
    provider_status="AUTHORIZED",
    provider_amount_minor=10000,
    provider_currency="ZAR",
    provider_reference="provider-ref-001",
    request_context=ctx,
)

if mismatch.state != "MISMATCH" or "status" not in mismatch.mismatch_fields:
    raise SystemExit("ERROR: reconciliation status mismatch was not detected")

cross_ctx = request_context.BaaSRequestContext(
    request_id="req-payments-cross",
    correlation_id="corr-payments-cross",
    service="payments",
    operation="payment.reconcile",
    organization_id="org-other",
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
    actor_id="actor-other",
    actor_type="SERVICE_ACCOUNT",
    kernel_authorization_ref="kernel_auth_payments_cross",
    idempotency_key="idem-payments-cross",
)

try:
    service.reconcile(
        payment_id=plan.payment_id,
        kernel_status="CAPTURED",
        kernel_amount_minor=10000,
        kernel_currency="ZAR",
        kernel_provider_reference="provider-ref-001",
        provider_status="CAPTURED",
        provider_amount_minor=10000,
        provider_currency="ZAR",
        provider_reference="provider-ref-001",
        request_context=cross_ctx,
    )
except payments.PaymentsBaaSError:
    pass
else:
    raise SystemExit("ERROR: cross-tenant payment access was accepted")

try:
    payments.ProviderConfiguration(
        provider_id="bad_provider",
        adapter_ref="adapter://bad",
        credential_ref="raw-secret-value",
        supported_currencies=("ZAR",),
        capabilities=("AUTHORIZE",),
    ).validate()
except payments.PaymentsBaaSError:
    pass
else:
    raise SystemExit("ERROR: raw provider credential was accepted")

status = (BAAS / "IMPLEMENTATION_STATUS.md").read_text(encoding="utf-8")
for phrase in [
    "- [x] Payment Abstraction",
    "- [x] Secret-reference provider credentials",
    "- [x] Explicit Kernel payment transition sequences",
    "- [x] Kernel refund validation boundary",
    "- [x] Payment reconciliation",
    "- [ ] Secrets",
]:
    if phrase not in status:
        raise SystemExit("ERROR: Payment Abstraction status missing: " + phrase)

print("OK: Provider-neutral registry and secret-reference credentials passed.")
print("OK: Payment planning is idempotent and adapter-only.")
print("OK: Immediate capture preserves explicit PENDING→AUTHORIZED→CAPTURED edges.")
print("OK: Kernel payment transition validation boundary passed.")
print("OK: Kernel refund invariant prevents over-refund.")
print("OK: Payment reconciliation detects mismatches.")
print("OK: Cross-tenant payment access fails closed.")
print("OK: No direct provider network execution is claimed.")
print("STATUS: BAAS P0 PAYMENT ABSTRACTION READY")
