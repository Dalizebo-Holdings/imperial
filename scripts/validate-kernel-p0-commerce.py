#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
KERNEL = ROOT / "kernel"

MODULES = {
    "kernel_commerce": KERNEL / "commerce/runtime.py",
    "kernel_migrations": KERNEL / "migrations/runtime.py",
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Kernel commerce runtime file: {path}"
        )
    py_compile.compile(str(path), doraise=True)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)

    if spec is None or spec.loader is None:
        raise SystemExit(
            f"ERROR: unable to load module: {path}"
        )

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


commerce = load_module(
    "kernel_commerce",
    MODULES["kernel_commerce"],
)
migrations = load_module(
    "kernel_migrations",
    MODULES["kernel_migrations"],
)

tenant = commerce.TenantScope(
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
)
tenant.validate()

resource = commerce.CommerceResource(
    id="variant-validation",
    entity_type="PRODUCT_VARIANT",
    tenant=tenant,
    created_at="2026-01-01T00:00:00+00:00",
    updated_at="2026-01-01T00:00:00+00:00",
)

variant = commerce.ProductVariant(
    resource=resource,
    product_id="product-validation",
    sku="SKU-VALIDATION",
    price=commerce.Money(
        amount_minor=1000,
        currency="ZAR",
    ),
)
variant.validate()

try:
    commerce.Money(
        amount_minor=-1,
        currency="ZAR",
    ).validate()
except commerce.CommercePrimitiveError:
    pass
else:
    raise SystemExit(
        "ERROR: negative money amount was accepted"
    )

inventory_resource = commerce.CommerceResource(
    id="inventory-validation",
    entity_type="INVENTORY_ITEM",
    tenant=tenant,
    created_at="2026-01-01T00:00:00+00:00",
    updated_at="2026-01-01T00:00:00+00:00",
)

inventory = commerce.InventoryItem(
    resource=inventory_resource,
    product_variant_id=resource.id,
    store_id="store-validation",
    branch_id="branch-validation",
    quantity_on_hand=10,
    quantity_reserved=3,
)
inventory.validate()

if inventory.quantity_available != 7:
    raise SystemExit(
        "ERROR: inventory available quantity is incorrect"
    )

try:
    commerce.InventoryItem(
        resource=inventory_resource,
        product_variant_id=resource.id,
        store_id="store-validation",
        branch_id=None,
        quantity_on_hand=1,
        quantity_reserved=2,
    ).validate()
except commerce.CommercePrimitiveError:
    pass
else:
    raise SystemExit(
        "ERROR: over-reserved inventory was accepted"
    )

order = commerce.OrderState(
    order_id="order-validation",
    status="DRAFT",
)
order = order.transition("PLACED")
order = order.transition("CONFIRMED")
order = order.transition("COMPLETED")

try:
    order.transition("CANCELLED")
except commerce.CommercePrimitiveError:
    pass
else:
    raise SystemExit(
        "ERROR: completed order allowed further transition"
    )

payment = commerce.PaymentState(
    payment_id="payment-validation",
    order_id="order-validation",
    status="PENDING",
    amount=commerce.Money(
        amount_minor=1000,
        currency="ZAR",
    ),
)

payment = payment.transition("AUTHORIZED")
payment = payment.transition("CAPTURED")

refund = commerce.Refund(
    refund_id="refund-validation",
    payment_id=payment.payment_id,
    amount=commerce.Money(
        amount_minor=400,
        currency="ZAR",
    ),
    reason="validation",
)

refund.validate(
    captured_amount=payment.amount,
    previously_refunded_minor=500,
)

try:
    refund.validate(
        captured_amount=payment.amount,
        previously_refunded_minor=700,
    )
except commerce.CommercePrimitiveError:
    pass
else:
    raise SystemExit(
        "ERROR: refund total above captured amount was accepted"
    )

commerce.Discount(
    discount_id="discount-fixed",
    discount_type="FIXED",
    value_minor=100,
    currency="ZAR",
).validate()

commerce.Discount(
    discount_id="discount-percent",
    discount_type="PERCENTAGE",
    basis_points=1500,
).validate()

if commerce.validate_cart_transition(
    "OPEN",
    "CONVERTED",
) != "CONVERTED":
    raise SystemExit(
        "ERROR: valid cart conversion failed"
    )

try:
    commerce.validate_cart_transition(
        "CONVERTED",
        "OPEN",
    )
except commerce.CommercePrimitiveError:
    pass
else:
    raise SystemExit(
        "ERROR: terminal cart reopened"
    )

sql_dir = KERNEL / "migrations/sql"
available = migrations.discover_migrations(sql_dir)
versions = [item.version for item in available]

if versions[:2] != [1, 2]:
    raise SystemExit(
        "ERROR: Kernel migrations do not include ordered 0001 + 0002"
    )

commerce_sql = (
    KERNEL
    / "migrations/sql/0002_kernel_commerce_primitives.sql"
).read_text(encoding="utf-8")

required_tables = [
    "kernel.stores",
    "kernel.branches",
    "kernel.products",
    "kernel.product_variants",
    "kernel.inventory_items",
    "kernel.customers",
    "kernel.carts",
    "kernel.orders",
    "kernel.order_items",
    "kernel.payments",
    "kernel.refunds",
    "kernel.discounts",
]

for table in required_tables:
    if table not in commerce_sql:
        raise SystemExit(
            "ERROR: commerce migration missing table: " + table
        )

for invariant in [
    "quantity_on_hand >= 0",
    "quantity_reserved <= quantity_on_hand",
    "price_minor >= 0",
    "amount_minor >= 0",
    "basis_points BETWEEN 1 AND 10000",
]:
    if invariant not in commerce_sql:
        raise SystemExit(
            "ERROR: commerce migration missing invariant: "
            + invariant
        )

status = (
    KERNEL / "IMPLEMENTATION_STATUS.md"
).read_text(encoding="utf-8")

for phrase in [
    "- [x] Commerce primitives",
    "## P0 Status",
    "COMPLETE",
    "Phase 5 — Dalizebo BaaS",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Kernel P0 closure status missing: " + phrase
        )

kernel_status = (
    KERNEL / "STATUS.md"
).read_text(encoding="utf-8")

if "Kernel P0 complete." not in kernel_status:
    raise SystemExit(
        "ERROR: Kernel status did not close P0"
    )

print("OK: Shared commerce money invariants passed.")
print("OK: Product Variant and Inventory primitives passed.")
print("OK: Inventory cannot become negative or over-reserved.")
print("OK: Order and cart terminal-state rules passed.")
print("OK: Payment/refund bounds passed.")
print("OK: Discount invariants passed.")
print("OK: Commerce migration contains all 12 canonical entities.")
print("OK: Migration order 0001 -> 0002 passed.")
print("OK: Kernel P0 checklist is complete.")
print("STATUS: KERNEL P0 COMPLETE")
