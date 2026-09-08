#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
SAAS = ROOT / "saas"
KERNEL = ROOT / "kernel"

MODULES = {
    "saas_product_context": SAAS / "runtime/product_context.py",
    "commerce_checkout": SAAS / "commerce/checkout/runtime.py",
    "kernel_commerce": KERNEL / "commerce/runtime.py",
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
checkout = load_module(
    "commerce_checkout",
    MODULES["commerce_checkout"],
)
kernel = load_module(
    "kernel_commerce",
    MODULES["kernel_commerce"],
)

planner = foundation.CommercePOSFoundation()

service = checkout.CommerceCartCheckoutOrdersService(
    foundation=planner,
    product_command_type=foundation.ProductCommand,
    kernel_tenant_scope_type=kernel.TenantScope,
    kernel_resource_type=kernel.CommerceResource,
    kernel_inventory_type=kernel.InventoryItem,
    kernel_money_type=kernel.Money,
    kernel_order_state_type=kernel.OrderState,
    kernel_cart_transition=kernel.validate_cart_transition,
    kernel_currency_validator=kernel.validate_currency,
)

context = foundation.ProductContext(
    product="COMMERCE",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_checkout_validation",
    correlation_id="corr-checkout-validation",
    store_id="store-validation",
)

def evidence(entity_type, entity_id, snapshot_suffix):
    return checkout.CommerceEvidence(
        source="kernel.commerce",
        entity_type=entity_type,
        entity_id=entity_id,
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
        environment_id=context.environment_id,
        snapshot_ref=f"kernel-snapshot://{snapshot_suffix}",
    )

store_evidence = evidence("STORE", "store-validation", "store")
customer_evidence = evidence("CUSTOMER", "customer-validation", "customer")
cart_evidence = evidence("CART", "cart-validation", "cart")

cart_result = service.plan_cart_create(
    context=context,
    request=checkout.CartCreateRequest(
        cart_id="cart-validation",
        store_id="store-validation",
        customer_id="customer-validation",
        currency="ZAR",
        idempotency_key="cart-validation-create",
        requested_at="2026-09-09T13:00:00+00:00",
    ),
    store_evidence=store_evidence,
    customer_evidence=customer_evidence,
)

if cart_result["plan"].entity_type != "CART":
    raise SystemExit("ERROR: Cart create entity mismatch")

line_one = checkout.CheckoutLineSnapshot(
    order_item_id="order-item-001",
    product_id="product-001",
    product_variant_id="variant-001",
    inventory_item_id="inventory-001",
    quantity=2,
    unit_price_minor=1500,
    currency="ZAR",
    expected_quantity_on_hand=10,
    expected_quantity_reserved=1,
    product_evidence=evidence("PRODUCT", "product-001", "product-001"),
    variant_evidence=evidence("PRODUCT_VARIANT", "variant-001", "variant-001"),
    inventory_evidence=evidence("INVENTORY_ITEM", "inventory-001", "inventory-001"),
)

line_two = checkout.CheckoutLineSnapshot(
    order_item_id="order-item-002",
    product_id="product-002",
    product_variant_id="variant-002",
    inventory_item_id="inventory-002",
    quantity=1,
    unit_price_minor=2500,
    currency="ZAR",
    expected_quantity_on_hand=5,
    expected_quantity_reserved=0,
    product_evidence=evidence("PRODUCT", "product-002", "product-002"),
    variant_evidence=evidence("PRODUCT_VARIANT", "variant-002", "variant-002"),
    inventory_evidence=evidence("INVENTORY_ITEM", "inventory-002", "inventory-002"),
)

request = checkout.CheckoutRequest(
    checkout_id="checkout-validation",
    cart_id="cart-validation",
    order_id="order-validation",
    store_id="store-validation",
    customer_id="customer-validation",
    currency="ZAR",
    lines=(line_one, line_two),
    idempotency_key="checkout-validation-1",
    requested_at="2026-09-09T13:01:00+00:00",
)

result = service.plan_checkout(
    context=context,
    request=request,
    store_evidence=store_evidence,
    cart_evidence=cart_evidence,
    customer_evidence=customer_evidence,
)

plan = result["plan"]

if plan.subtotal_minor != 5500 or plan.total_minor != 5500:
    raise SystemExit("ERROR: checkout total calculation failed")

if plan.discount_minor != 0 or plan.tax_minor != 0:
    raise SystemExit("ERROR: deferred discount/tax fields are not zero")

if plan.transaction_requirement != "KERNEL_ATOMIC_TRANSACTION":
    raise SystemExit("ERROR: atomic checkout requirement missing")

if plan.event_publication != "OUTBOX_AFTER_COMMIT":
    raise SystemExit("ERROR: post-commit event requirement missing")

if len(plan.inventory_reservations) != 2:
    raise SystemExit("ERROR: inventory reservation plan count mismatch")

if (
    plan.inventory_reservations[0].input_metadata["target_quantity_reserved"]
    != 3
):
    raise SystemExit("ERROR: checkout inventory reservation target mismatch")

if len(plan.order_items) != 2:
    raise SystemExit("ERROR: Order Item plan count mismatch")

if (
    plan.order_items[0].input_metadata["total_minor"]
    != 3000
):
    raise SystemExit("ERROR: Order Item line total mismatch")

if plan.cart_transition.input_metadata["to_status"] != "CONVERTED":
    raise SystemExit("ERROR: Cart did not plan OPEN→CONVERTED")

if plan.order_transition.input_metadata["to_status"] != "PLACED":
    raise SystemExit("ERROR: Order did not plan DRAFT→PLACED")

duplicate = service.plan_checkout(
    context=context,
    request=request,
    store_evidence=store_evidence,
    cart_evidence=cart_evidence,
    customer_evidence=customer_evidence,
)

if (
    duplicate["created"] is not False
    or duplicate["plan"].transaction_id != plan.transaction_id
):
    raise SystemExit("ERROR: checkout transaction idempotency failed")

try:
    service.plan_checkout(
        context=context,
        request=checkout.CheckoutRequest(
            checkout_id="checkout-validation",
            cart_id="cart-validation",
            order_id="order-validation",
            store_id="store-validation",
            customer_id="customer-validation",
            currency="ZAR",
            lines=(
                checkout.CheckoutLineSnapshot(
                    **{
                        **line_one.__dict__,
                        "quantity": 3,
                    }
                ),
                line_two,
            ),
            idempotency_key="checkout-validation-1",
            requested_at="2026-09-09T13:01:00+00:00",
        ),
        store_evidence=store_evidence,
        cart_evidence=cart_evidence,
        customer_evidence=customer_evidence,
    )
except checkout.CommerceCheckoutError:
    pass
else:
    raise SystemExit(
        "ERROR: checkout idempotency conflict was accepted"
    )

try:
    service.plan_checkout(
        context=context,
        request=checkout.CheckoutRequest(
            checkout_id="checkout-insufficient",
            cart_id="cart-validation",
            order_id="order-insufficient",
            store_id="store-validation",
            customer_id="customer-validation",
            currency="ZAR",
            lines=(
                checkout.CheckoutLineSnapshot(
                    order_item_id="order-item-insufficient",
                    product_id="product-001",
                    product_variant_id="variant-001",
                    inventory_item_id="inventory-001",
                    quantity=10,
                    unit_price_minor=1500,
                    currency="ZAR",
                    expected_quantity_on_hand=10,
                    expected_quantity_reserved=1,
                    product_evidence=line_one.product_evidence,
                    variant_evidence=line_one.variant_evidence,
                    inventory_evidence=line_one.inventory_evidence,
                ),
            ),
            idempotency_key="checkout-insufficient",
            requested_at="2026-09-09T13:02:00+00:00",
        ),
        store_evidence=store_evidence,
        cart_evidence=cart_evidence,
        customer_evidence=customer_evidence,
    )
except checkout.CommerceCheckoutError:
    pass
else:
    raise SystemExit(
        "ERROR: checkout reserved more than available inventory"
    )

try:
    service.plan_checkout(
        context=context,
        request=checkout.CheckoutRequest(
            checkout_id="checkout-currency",
            cart_id="cart-validation",
            order_id="order-currency",
            store_id="store-validation",
            customer_id="customer-validation",
            currency="ZAR",
            lines=(
                checkout.CheckoutLineSnapshot(
                    **{
                        **line_one.__dict__,
                        "currency": "USD",
                    }
                ),
            ),
            idempotency_key="checkout-currency",
            requested_at="2026-09-09T13:03:00+00:00",
        ),
        store_evidence=store_evidence,
        cart_evidence=cart_evidence,
        customer_evidence=customer_evidence,
    )
except checkout.CommerceCheckoutError:
    pass
else:
    raise SystemExit(
        "ERROR: mixed checkout currency was accepted"
    )

cross_cart = checkout.CommerceEvidence(
    source="kernel.commerce",
    entity_type="CART",
    entity_id="cart-validation",
    organization_id="org-other",
    workspace_id=context.workspace_id,
    project_id=context.project_id,
    environment_id=context.environment_id,
    snapshot_ref="kernel-snapshot://cross-cart",
)

try:
    service.plan_checkout(
        context=context,
        request=checkout.CheckoutRequest(
            checkout_id="checkout-cross",
            cart_id="cart-validation",
            order_id="order-cross",
            store_id="store-validation",
            customer_id="customer-validation",
            currency="ZAR",
            lines=(line_one,),
            idempotency_key="checkout-cross",
            requested_at="2026-09-09T13:04:00+00:00",
        ),
        store_evidence=store_evidence,
        cart_evidence=cross_cart,
        customer_evidence=customer_evidence,
    )
except checkout.CommerceCheckoutError:
    pass
else:
    raise SystemExit(
        "ERROR: cross-tenant Cart evidence was accepted"
    )

order_evidence = evidence("ORDER", "order-validation", "order")
confirmed = service.plan_order_transition(
    context=context,
    order_evidence=order_evidence,
    current_status="PLACED",
    target_status="CONFIRMED",
    idempotency_key="order-validation-confirm",
    requested_at="2026-09-09T13:05:00+00:00",
)

if confirmed["plan"].input_metadata["to_status"] != "CONFIRMED":
    raise SystemExit("ERROR: valid Order transition failed")

try:
    service.plan_order_transition(
        context=context,
        order_evidence=order_evidence,
        current_status="DRAFT",
        target_status="COMPLETED",
        idempotency_key="order-validation-illegal",
        requested_at="2026-09-09T13:06:00+00:00",
    )
except checkout.CommerceCheckoutError:
    pass
else:
    raise SystemExit(
        "ERROR: illegal Order lifecycle transition was accepted"
    )

status = (
    SAAS / "IMPLEMENTATION_STATUS.md"
).read_text(encoding="utf-8")

for phrase in [
    "- [x] Cart",
    "- [x] Checkout",
    "- [x] Orders",
    "- [x] Composite atomic checkout transaction requirement",
    "- [ ] Durable Kernel Cart Item primitive",
    "- [ ] Payments",
    "Commerce P0 — Payments + Discounts + Notifications + Dashboard.",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Cart/Checkout/Orders status missing: " + phrase
        )

print("OK: Cart create/terminal lifecycle planning passed.")
print("OK: Checkout line price and currency validation passed.")
print("OK: Inventory reservation respects Kernel availability invariants.")
print("OK: Order/Order Item integer minor-unit calculations passed.")
print("OK: Cart conversion + Order placement are in one atomic transaction plan.")
print("OK: Checkout transaction idempotency/conflict detection passed.")
print("OK: Cross-tenant checkout evidence fails closed.")
print("OK: Kernel Order lifecycle validation passed.")
print("STATUS: COMMERCE P0 CART + CHECKOUT + ORDERS READY")
