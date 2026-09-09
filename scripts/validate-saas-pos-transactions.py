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

MODULES = {
    "saas.runtime.product_context": (
        SAAS / "runtime/product_context.py"
    ),
    "saas.pos.foundation.runtime": (
        SAAS / "pos/foundation/runtime.py"
    ),
    "saas.pos.transactions.runtime": (
        SAAS / "pos/transactions/runtime.py"
    ),
    "kernel.commerce.runtime": (
        KERNEL / "commerce/runtime.py"
    ),
    "baas.payments.runtime": (
        BAAS / "payments/runtime.py"
    ),
    "baas.runtime.request_context": (
        BAAS / "runtime/request_context.py"
    ),
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing POS transaction runtime file: {path}"
        )
    py_compile.compile(
        str(path),
        doraise=True,
    )


def load_module(name):
    try:
        return importlib.import_module(name)
    except Exception as exc:
        raise SystemExit(
            f"ERROR: unable to import package module {name}: {exc}"
        ) from exc


foundation = load_module(
    "saas.runtime.product_context"
)
pos_foundation = load_module(
    "saas.pos.foundation.runtime"
)
transactions = load_module(
    "saas.pos.transactions.runtime"
)
kernel = load_module(
    "kernel.commerce.runtime"
)
baas_payments = load_module(
    "baas.payments.runtime"
)
baas_context = load_module(
    "baas.runtime.request_context"
)


class FakeStaffAccess:
    def __init__(self):
        self.permissions = {
            "staff-validation": {
                "pos.cart.create",
                "pos.cart.update",
                "pos.checkout.execute",
                "pos.payment.cash.record",
                "pos.payment.card.record",
                "pos.receipt.issue",
            }
        }

    def check(self, context, actor_id, permission):
        return (
            actor_id == context.actor_id
            and permission in self.permissions.get(actor_id, set())
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


payment_abstraction = (
    baas_payments.PaymentAbstractionService(
        kernel_transition_validator=(
            kernel_transition_validator
        ),
        kernel_refund_validator=(
            kernel_refund_validator
        ),
    )
)

provider_context = baas_context.BaaSRequestContext(
    request_id="req-pos-provider",
    correlation_id="corr-pos-transaction-validation",
    service="payments",
    operation="provider.register",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="staff-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_pos_transaction_validation",
    idempotency_key="provider-validation",
)

payment_abstraction.register_provider(
    provider=baas_payments.ProviderConfiguration(
        provider_id="provider_validation",
        adapter_ref="adapter://payments/validation",
        credential_ref="vault://payments/validation/control",
        supported_currencies=("ZAR",),
        capabilities=(
            "AUTHORIZE",
            "CAPTURE",
            "REFUND",
        ),
    ),
    request_context=provider_context,
)

planner = foundation.CommercePOSFoundation()
access = FakeStaffAccess()

service = transactions.POSTransactionService(
    foundation=planner,
    product_command_type=foundation.ProductCommand,
    staff_permission_checker=access.check,
    kernel_tenant_scope_type=kernel.TenantScope,
    kernel_resource_type=kernel.CommerceResource,
    kernel_inventory_type=kernel.InventoryItem,
    kernel_money_type=kernel.Money,
    kernel_order_state_type=kernel.OrderState,
    kernel_payment_state_type=kernel.PaymentState,
    kernel_cart_transition=kernel.validate_cart_transition,
    kernel_currency_validator=kernel.validate_currency,
    baas_payment_service=payment_abstraction,
    baas_payment_request_type=baas_payments.PaymentRequest,
    baas_request_context_type=baas_context.BaaSRequestContext,
)

context = foundation.ProductContext(
    product="POS",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="staff-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_pos_transaction_validation",
    correlation_id="corr-pos-transaction-validation",
    store_id="store-validation",
    branch_id="branch-validation",
)


def evidence(
    entity_type,
    entity_id,
    *,
    status=None,
):
    return transactions.Evidence(
        source="kernel.commerce",
        entity_type=entity_type,
        entity_id=entity_id,
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
        environment_id=context.environment_id,
        snapshot_ref=(
            f"kernel-snapshot://{entity_type.lower()}/{entity_id}"
        ),
        status=status,
    )


store_evidence = evidence(
    "STORE",
    "store-validation",
    status="ACTIVE",
)
customer_evidence = evidence(
    "CUSTOMER",
    "customer-validation",
)

opened = service.open_cart(
    context=context,
    cart_id="cart-validation",
    currency="ZAR",
    customer_id="customer-validation",
    store_evidence=store_evidence,
    customer_evidence=customer_evidence,
    idempotency_key="cart-validation-create",
    requested_at="2026-09-09T16:00:00+00:00",
)

if (
    opened["plan"].entity_type
    != "CART"
):
    raise SystemExit(
        "ERROR: POS Cart did not use shared Cart authority"
    )

line = transactions.POSCartLine(
    line_id="line-001",
    order_item_id="order-item-001",
    product_id="product-001",
    product_variant_id="variant-001",
    inventory_item_id="inventory-001",
    quantity=2,
    unit_price_minor=2500,
    currency="ZAR",
    expected_quantity_on_hand=10,
    expected_quantity_reserved=1,
    product_evidence=evidence(
        "PRODUCT",
        "product-001",
        status="ACTIVE",
    ),
    variant_evidence=evidence(
        "PRODUCT_VARIANT",
        "variant-001",
    ),
    inventory_evidence=evidence(
        "INVENTORY_ITEM",
        "inventory-001",
    ),
)

session = service.upsert_cart_line(
    context=context,
    cart_id="cart-validation",
    line=line,
    updated_at="2026-09-09T16:01:00+00:00",
)

if len(session.lines) != 1:
    raise SystemExit(
        "ERROR: POS transient Cart line update failed"
    )

cart_evidence = evidence(
    "CART",
    "cart-validation",
    status="OPEN",
)

checkout_result = service.plan_checkout(
    context=context,
    checkout_id="checkout-validation",
    cart_evidence=cart_evidence,
    order_id="order-validation",
    idempotency_key="checkout-validation",
    requested_at="2026-09-09T16:02:00+00:00",
)

checkout = checkout_result["plan"]

if checkout.total_minor != 5000:
    raise SystemExit(
        "ERROR: POS checkout total calculation failed"
    )

if (
    checkout.order_create.input_metadata["branch_id"]
    != "branch-validation"
):
    raise SystemExit(
        "ERROR: POS Order branch_id missing"
    )

if (
    checkout.inventory_reservations[0].input_metadata[
        "target_quantity_reserved"
    ]
    != 3
):
    raise SystemExit(
        "ERROR: POS inventory reservation target mismatch"
    )

if checkout.transaction_requirement != "KERNEL_ATOMIC_TRANSACTION":
    raise SystemExit(
        "ERROR: POS checkout atomic transaction requirement missing"
    )

duplicate_checkout = service.plan_checkout(
    context=context,
    checkout_id="checkout-validation",
    cart_evidence=cart_evidence,
    order_id="order-validation",
    idempotency_key="checkout-validation",
    requested_at="2026-09-09T16:02:00+00:00",
)

if (
    duplicate_checkout["created"] is not False
    or duplicate_checkout["plan"].transaction_id
    != checkout.transaction_id
):
    raise SystemExit(
        "ERROR: POS checkout idempotency failed"
    )

order_evidence = evidence(
    "ORDER",
    "order-validation",
    status="PLACED",
)

cash = service.plan_cash_settlement(
    context=context,
    checkout_plan=checkout,
    order_evidence=order_evidence,
    tendered_minor=6000,
    idempotency_key="cash-validation",
    settled_at="2026-09-09T16:03:00+00:00",
)

cash_plan = cash["plan"]

cash_targets = [
    item.input_metadata["to_status"]
    for item in cash_plan.payment_transitions
]

if cash_targets != [
    "AUTHORIZED",
    "CAPTURED",
]:
    raise SystemExit(
        "ERROR: cash Payment lifecycle was not explicit"
    )

if cash_plan.receipt.change_minor != 1000:
    raise SystemExit(
        "ERROR: cash change calculation failed"
    )

if (
    cash_plan.inventory_deductions[0].input_metadata[
        "target_quantity_on_hand"
    ]
    != 8
    or cash_plan.inventory_deductions[0].input_metadata[
        "target_quantity_reserved"
    ]
    != 1
):
    raise SystemExit(
        "ERROR: POS inventory deduction did not consume reservation"
    )

order_targets = [
    item.input_metadata["to_status"]
    for item in cash_plan.order_transitions
]

if order_targets != [
    "CONFIRMED",
    "COMPLETED",
]:
    raise SystemExit(
        "ERROR: POS successful settlement did not complete Order explicitly"
    )

if (
    cash_plan.receipt.state
    != "READY_FOR_RECEIPT_RENDERER_AFTER_COMMIT"
):
    raise SystemExit(
        "ERROR: receipt rendering is not post-commit"
    )

try:
    service.plan_cash_settlement(
        context=context,
        checkout_plan=checkout,
        order_evidence=order_evidence,
        tendered_minor=4999,
        idempotency_key="cash-insufficient",
        settled_at="2026-09-09T16:04:00+00:00",
    )
except transactions.POSTransactionError:
    pass
else:
    raise SystemExit(
        "ERROR: insufficient cash tender was accepted"
    )

card = service.plan_card_payment(
    context=context,
    checkout_plan=checkout,
    order_evidence=order_evidence,
    provider_id="provider_validation",
    payment_request_id="pos-card-request",
    idempotency_key="pos-card-validation",
    requested_at="2026-09-09T16:05:00+00:00",
)

if (
    card.provider_operation_plan.state
    != "READY_FOR_PROVIDER_ADAPTER"
):
    raise SystemExit(
        "ERROR: POS Card payment claimed provider execution"
    )

if (
    "credential"
    in str(
        card.payment_create.input_metadata
    ).lower()
):
    raise SystemExit(
        "ERROR: provider credential leaked into POS Payment metadata"
    )

payment_evidence = evidence(
    "PAYMENT",
    card.payment_id,
)

provider_result = baas_payments.ProviderResult(
    payment_id=card.payment_id,
    provider_id="provider_validation",
    provider_reference="provider-ref-pos-validation",
    outcome="CAPTURED",
    amount_minor=5000,
    currency="ZAR",
    occurred_at="2026-09-09T16:05:05+00:00",
)

card_settlement = service.plan_card_result(
    context=context,
    checkout_plan=checkout,
    order_evidence=order_evidence,
    payment_evidence=payment_evidence,
    provider_result=provider_result,
    kernel_payment_status="PENDING",
    settled_at="2026-09-09T16:05:06+00:00",
)

if not isinstance(
    card_settlement,
    transactions.POSSettlementPlan,
):
    raise SystemExit(
        "ERROR: captured Card payment did not create settlement plan"
    )

card_targets = [
    item.input_metadata["to_status"]
    for item in card_settlement.payment_transitions
]

if card_targets != [
    "AUTHORIZED",
    "CAPTURED",
]:
    raise SystemExit(
        "ERROR: Card Payment lifecycle was not explicit"
    )

if (
    card_settlement.receipt.tender_type
    != "CARD"
    or card_settlement.receipt.provider_reference
    != "provider-ref-pos-validation"
):
    raise SystemExit(
        "ERROR: Card receipt metadata mismatch"
    )

if hasattr(
    card_settlement.receipt,
    "card_number",
):
    raise SystemExit(
        "ERROR: Receipt exposes card_number"
    )

cross_order = transactions.Evidence(
    source="kernel.commerce",
    entity_type="ORDER",
    entity_id="order-validation",
    organization_id="org-other",
    workspace_id=context.workspace_id,
    project_id=context.project_id,
    environment_id=context.environment_id,
    snapshot_ref="kernel-snapshot://order/cross",
    status="PLACED",
)

try:
    service.plan_cash_settlement(
        context=context,
        checkout_plan=checkout,
        order_evidence=cross_order,
        tendered_minor=5000,
        idempotency_key="cash-cross",
        settled_at="2026-09-09T16:06:00+00:00",
    )
except transactions.POSTransactionError:
    pass
else:
    raise SystemExit(
        "ERROR: cross-tenant Order evidence was accepted"
    )

status = (
    SAAS / "IMPLEMENTATION_STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "- [x] Cart",
    "- [x] Checkout",
    "- [x] Cash payment recording",
    "- [x] Card payment recording",
    "- [x] Receipts",
    "- [x] Inventory deduction",
    "- [x] Returns",
    "- [x] Daily summaries",
    "DALIZEBO POS P0: COMPLETE",
    "PHASE 6: COMPLETE",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: POS transaction status missing: "
            + phrase
        )

print("OK: POS Cart reuses shared Kernel Cart authority.")
print("OK: Branch-scoped transient Cart line workflow passed.")
print("OK: POS checkout reserves inventory and places Order atomically.")
print("OK: Cash Payment preserves PENDING→AUTHORIZED→CAPTURED.")
print("OK: Cash tender/change and receipt planning passed.")
print("OK: Card payment delegates to BaaS Payment Abstraction.")
print("OK: Card Payment transitions remain explicit.")
print("OK: Successful settlement deducts inventory reservation atomically.")
print("OK: Order PLACED→CONFIRMED→COMPLETED remains explicit.")
print("OK: Receipt rendering is post-commit and credential-safe.")
print("STATUS: POS P0 CART + CHECKOUT + PAYMENTS + RECEIPTS READY")
