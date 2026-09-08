#!/usr/bin/env python3
from pathlib import Path
from dataclasses import dataclass
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
SAAS = ROOT / "saas"
KERNEL = ROOT / "kernel"
BAAS = ROOT / "baas"

MODULES = {
    "saas_product_context": SAAS / "runtime/product_context.py",
    "commerce_checkout": SAAS / "commerce/checkout/runtime.py",
    "commerce_operations": SAAS / "commerce/operations/runtime.py",
    "kernel_commerce": KERNEL / "commerce/runtime.py",
    "baas_payments": BAAS / "payments/runtime.py",
    "baas_request_context": BAAS / "runtime/request_context.py",
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(f"ERROR: missing runtime file: {path}")
    py_compile.compile(str(path), doraise=True)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"ERROR: unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


foundation = load_module(
    "saas_product_context",
    MODULES["saas_product_context"],
)
checkout_module = load_module(
    "commerce_checkout",
    MODULES["commerce_checkout"],
)
operations = load_module(
    "commerce_operations",
    MODULES["commerce_operations"],
)
kernel = load_module(
    "kernel_commerce",
    MODULES["kernel_commerce"],
)
baas_payments = load_module(
    "baas_payments",
    MODULES["baas_payments"],
)
baas_context = load_module(
    "baas_request_context",
    MODULES["baas_request_context"],
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


def kernel_refund_validator(*args):
    return True


payment_abstraction = baas_payments.PaymentAbstractionService(
    kernel_transition_validator=kernel_transition_validator,
    kernel_refund_validator=kernel_refund_validator,
)

provider_context = baas_context.BaaSRequestContext(
    request_id="req-provider-validation",
    correlation_id="corr-operations-validation",
    service="payments",
    operation="provider.register",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="SERVICE_ACCOUNT",
    kernel_authorization_ref="kernel_auth_operations_validation",
    idempotency_key="provider-validation",
)

payment_abstraction.register_provider(
    provider=baas_payments.ProviderConfiguration(
        provider_id="provider_validation",
        adapter_ref="adapter://payments/validation",
        credential_ref="vault://payments/validation/control",
        supported_currencies=("ZAR",),
        capabilities=("AUTHORIZE", "CAPTURE", "REFUND"),
    ),
    request_context=provider_context,
)

planner = foundation.CommercePOSFoundation()

context = foundation.ProductContext(
    product="COMMERCE",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_operations_validation",
    correlation_id="corr-operations-validation",
    store_id="store-validation",
)


def evidence(entity_type, entity_id):
    return operations.CommerceEvidence(
        source="kernel.commerce",
        entity_type=entity_type,
        entity_id=entity_id,
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
        environment_id=context.environment_id,
    )


payments_service = operations.CommercePaymentsService(
    foundation=planner,
    product_command_type=foundation.ProductCommand,
    baas_payment_service=payment_abstraction,
    baas_payment_request_type=baas_payments.PaymentRequest,
    baas_request_context_type=baas_context.BaaSRequestContext,
    kernel_order_state_type=kernel.OrderState,
)

order_evidence = evidence("ORDER", "order-validation")

payment = payments_service.plan_payment(
    context=context,
    order_evidence=order_evidence,
    order_status="PLACED",
    provider_id="provider_validation",
    payment_request_id="payment-request-validation",
    amount_minor=9000,
    currency="ZAR",
    capture_mode="AUTHORIZE_CAPTURE",
    idempotency_key="commerce-payment-validation",
    requested_at="2026-09-09T14:00:00+00:00",
)

if payment.payment_record_command.entity_type != "PAYMENT":
    raise SystemExit("ERROR: shared Payment creation command missing")

if payment.provider_operation_plan.state != "READY_FOR_PROVIDER_ADAPTER":
    raise SystemExit("ERROR: Commerce claimed provider execution")

if "credential" in str(payment.payment_record_command.input_metadata).lower():
    raise SystemExit("ERROR: provider credential leaked into Commerce metadata")

provider_result = baas_payments.ProviderResult(
    payment_id=payment.payment_id,
    provider_id="provider_validation",
    provider_reference="provider-ref-validation",
    outcome="CAPTURED",
    amount_minor=9000,
    currency="ZAR",
    occurred_at="2026-09-09T14:00:05+00:00",
)

payment_evidence = evidence("PAYMENT", payment.payment_id)

result = payments_service.plan_provider_result(
    context=context,
    order_evidence=order_evidence,
    payment_evidence=payment_evidence,
    provider_result=provider_result,
    kernel_payment_status="PENDING",
)

transitions = [
    item.input_metadata["to_status"]
    for item in result.payment_transition_commands
]

if transitions != ["AUTHORIZED", "CAPTURED"]:
    raise SystemExit(
        "ERROR: Commerce did not preserve explicit payment transitions"
    )

if result.order_confirmation_command is None:
    raise SystemExit("ERROR: captured payment did not confirm Order")

if (
    result.order_confirmation_command.input_metadata["to_status"]
    != "CONFIRMED"
):
    raise SystemExit("ERROR: Order confirmation transition mismatch")

try:
    payments_service.plan_payment(
        context=context,
        order_evidence=order_evidence,
        order_status="DRAFT",
        provider_id="provider_validation",
        payment_request_id="payment-draft",
        amount_minor=1000,
        currency="ZAR",
        capture_mode="AUTHORIZE_CAPTURE",
        idempotency_key="payment-draft",
        requested_at="2026-09-09T14:01:00+00:00",
    )
except operations.CommerceOperationsError:
    pass
else:
    raise SystemExit("ERROR: payment started before Order PLACED")

discount_service = operations.CommerceDiscountsService(
    foundation=planner,
    product_command_type=foundation.ProductCommand,
    kernel_discount_type=kernel.Discount,
    kernel_currency_validator=kernel.validate_currency,
)

percentage = operations.DiscountDefinition(
    discount_id="discount-validation",
    discount_type="PERCENTAGE",
    value_minor=None,
    basis_points=1000,
    currency=None,
    idempotency_key="discount-validation-create",
)

discount_service.plan_create(
    context=context,
    definition=percentage,
    requested_at="2026-09-09T14:02:00+00:00",
)

quote = discount_service.quote(
    definition=percentage,
    subtotal_minor=10001,
    currency="ZAR",
)

if quote.discount_minor != 1000 or quote.total_minor != 9001:
    raise SystemExit("ERROR: percentage discount integer calculation failed")

fixed = operations.DiscountDefinition(
    discount_id="discount-fixed",
    discount_type="FIXED",
    value_minor=20000,
    basis_points=None,
    currency="ZAR",
    idempotency_key="discount-fixed-create",
)

fixed_quote = discount_service.quote(
    definition=fixed,
    subtotal_minor=5000,
    currency="ZAR",
)

if fixed_quote.discount_minor != 5000 or fixed_quote.total_minor != 0:
    raise SystemExit("ERROR: fixed discount did not cap at subtotal")

@dataclass(frozen=True)
class FakeCommand:
    input_metadata: dict

@dataclass(frozen=True)
class FakeCheckout:
    transaction_id: str
    subtotal_minor: int
    tax_minor: int
    currency: str
    order_create: FakeCommand
    state: str = "READY_FOR_KERNEL_TRANSACTION_ADAPTER"

overlay = discount_service.overlay_checkout(
    checkout_plan=FakeCheckout(
        transaction_id="checkout-tx-validation",
        subtotal_minor=10001,
        tax_minor=0,
        currency="ZAR",
        order_create=FakeCommand(
            input_metadata={
                "status": "DRAFT",
                "subtotal_minor": 10001,
                "discount_minor": 0,
                "tax_minor": 0,
                "total_minor": 10001,
            }
        ),
    ),
    quote=quote,
)

if (
    overlay.order_create_override.input_metadata["discount_minor"]
    != 1000
    or overlay.total_minor != 9001
):
    raise SystemExit("ERROR: checkout discount overlay failed")

notifications = operations.CommerceNotificationsService()

notification = notifications.plan(
    context=context,
    request=operations.NotificationRequest(
        event_type="order.confirmed",
        resource_type="ORDER",
        resource_id="order-validation",
        template_ref="template://commerce/order-confirmed/v1",
        recipient_ref="customer://customer-validation",
        channel="WEBHOOK",
        target_ref="webhook://commerce/order-events",
        idempotency_key="notify-order-validation-confirmed",
        occurred_at="2026-09-09T14:03:00+00:00",
    ),
)

if (
    notification["plan"].publication
    != "OUTBOX_AFTER_COMMIT"
):
    raise SystemExit("ERROR: notification is not post-commit")

duplicate_notification = notifications.plan(
    context=context,
    request=operations.NotificationRequest(
        event_type="order.confirmed",
        resource_type="ORDER",
        resource_id="order-validation",
        template_ref="template://commerce/order-confirmed/v1",
        recipient_ref="customer://customer-validation",
        channel="WEBHOOK",
        target_ref="webhook://commerce/order-events",
        idempotency_key="notify-order-validation-confirmed",
        occurred_at="2026-09-09T14:03:00+00:00",
    ),
)

if (
    duplicate_notification["created"] is not False
    or duplicate_notification["plan"].notification_id
    != notification["plan"].notification_id
):
    raise SystemExit("ERROR: notification idempotency failed")

try:
    notifications.plan(
        context=context,
        request=operations.NotificationRequest(
            event_type="order.confirmed",
            resource_type="ORDER",
            resource_id="order-validation",
            template_ref="template://commerce/order-confirmed/v1",
            recipient_ref="customer@example.com",
            channel="WEBHOOK",
            target_ref="webhook://commerce/order-events",
            idempotency_key="raw-email-notification",
            occurred_at="2026-09-09T14:03:00+00:00",
        ),
    )
except operations.CommerceOperationsError:
    pass
else:
    raise SystemExit("ERROR: raw notification recipient contact was accepted")

dashboard = operations.CommerceDashboardService(
    kernel_currency_validator=kernel.validate_currency,
)

read_plan = dashboard.plan(
    context=context,
    query=operations.DashboardQuery(
        period_start="2026-09-01T00:00:00+00:00",
        period_end="2026-10-01T00:00:00+00:00",
        currency="ZAR",
        low_stock_threshold=5,
    ),
)

if read_plan.state != "READY_FOR_DASHBOARD_READ_ADAPTER":
    raise SystemExit("ERROR: Dashboard claimed authoritative analytics state")

if "kernel.commerce.orders" not in read_plan.sources:
    raise SystemExit("ERROR: Dashboard Order source missing")

if read_plan.currency != "ZAR":
    raise SystemExit("ERROR: Dashboard currency scope failed")

try:
    dashboard.plan(
        context=context,
        query=operations.DashboardQuery(
            period_start="2025-01-01T00:00:00+00:00",
            period_end="2026-09-09T00:00:00+00:00",
            currency="ZAR",
        ),
    )
except operations.CommerceOperationsError:
    pass
else:
    raise SystemExit("ERROR: unbounded Dashboard query window was accepted")

status = (
    SAAS / "IMPLEMENTATION_STATUS.md"
).read_text(encoding="utf-8")

for phrase in [
    "- [x] Payments",
    "- [x] Discounts",
    "- [x] Notifications",
    "- [x] Dashboard",
    "DALIZEBO COMMERCE P0: COMPLETE",
    "POS P0 — Branches + Staff + Roles + Product Search.",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Commerce completion status missing: " + phrase
        )

print("OK: Commerce delegates payment planning to BaaS Payment Abstraction.")
print("OK: PENDING→AUTHORIZED→CAPTURED remains explicit.")
print("OK: Captured payment explicitly confirms PLACED Order.")
print("OK: Kernel FIXED/PERCENTAGE Discount validation passed.")
print("OK: Deterministic discount quote + checkout overlay passed.")
print("OK: Notifications are idempotent and post-commit only.")
print("OK: Raw recipient contact data is rejected from notification plans.")
print("OK: Dashboard remains a bounded, currency-scoped read projection.")
print("STATUS: COMMERCE P0 OPERATIONS READY")
print("STATUS: DALIZEBO COMMERCE P0 COMPLETE")
