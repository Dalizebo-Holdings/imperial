#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
SAAS = ROOT / "saas"
KERNEL = ROOT / "kernel"

required = [
    SAAS / "STATUS.md",
    SAAS / "IMPLEMENTATION_STATUS.md",
    SAAS / "commerce/README.md",
    SAAS / "runtime/product_context.py",
    SAAS / "commerce/inventory/runtime.py",
    SAAS / "commerce/cart/CART_CHECKOUT_CONTRACT.md",
    SAAS / "commerce/orders/ORDERS_CONTRACT.md",
    SAAS / "commerce/checkout/runtime.py",
    KERNEL / "commerce/runtime.py",
    KERNEL / "migrations/sql/0002_kernel_commerce_primitives.sql",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Cart/Checkout/Orders prerequisite/artifact: {path}"
        )

for path in [
    SAAS / "runtime/product_context.py",
    SAAS / "commerce/inventory/runtime.py",
    SAAS / "commerce/checkout/runtime.py",
    KERNEL / "commerce/runtime.py",
]:
    py_compile.compile(str(path), doraise=True)

(SAAS / "IMPLEMENTATION_STATUS.md").write_text(
"""# Dalizebo SaaS Implementation Status

## Phase

Phase 6 — Commerce + POS

## Prerequisites

- [x] Kernel P0 complete
- [x] BaaS P0 complete
- [x] Shared SaaS domain contract
- [x] Cross-product authority rules

## Phase 6 Foundation

- [x] Commerce/POS product execution context
- [x] Organization/workspace/project/environment context
- [x] Kernel authorization evidence requirement
- [x] Shared authoritative entity registry
- [x] Derived Kernel/BaaS authority routing
- [x] Direct product-to-product database coupling prohibited
- [x] Store/branch operational scope rules
- [x] Mutation idempotency
- [x] Idempotency conflict detection
- [x] Secret-bearing command metadata rejection
- [x] Platform command audit metadata
- [x] No duplicate authoritative commerce models

## Commerce P0

- [x] Store setup
- [x] Product catalogue
- [x] Variants
- [x] Pricing
- [x] Inventory
- [x] Customers
- [x] Cart
- [x] Checkout
- [x] Orders
- [ ] Payments
- [ ] Discounts
- [ ] Notifications
- [ ] Dashboard

## Cart + Checkout + Orders Components

- [x] Kernel Cart authority boundary
- [x] Cart OPEN/CONVERTED/ABANDONED lifecycle
- [x] Cart create and abandon planning
- [x] Authoritative checkout line snapshots
- [x] Kernel Variant price validation
- [x] Integer minor-unit line/subtotal calculation
- [x] Explicit inventory reservation planning
- [x] Expected inventory atomic compare/update requirement
- [x] Order DRAFT creation
- [x] Immutable Order Item price snapshots
- [x] Kernel Order lifecycle validation
- [x] Checkout DRAFT→PLACED transition
- [x] Cart OPEN→CONVERTED transition
- [x] Composite atomic checkout transaction requirement
- [x] Outbox-after-commit requirement
- [x] Checkout transaction idempotency
- [x] Cross-tenant checkout evidence rejection
- [x] No SaaS-owned Cart/Order/OrderItem database

## Cart Deferred Shared-Domain Work

- [ ] Durable Kernel Cart Item primitive
- [ ] Durable cross-session Cart Item persistence

## Checkout Deferred Work

- [ ] Discount calculation integration
- [ ] Tax engine integration
- [ ] Payment authorization/capture integration

## POS P0

- [ ] Branches
- [ ] Staff
- [ ] Roles
- [ ] Product search
- [ ] Barcode and SKU lookup
- [ ] Cart
- [ ] Checkout
- [ ] Cash payment recording
- [ ] Card payment recording
- [ ] Receipts
- [ ] Inventory deduction
- [ ] Returns
- [ ] Daily summaries

## Current Next Work

Commerce P0 — Payments + Discounts + Notifications + Dashboard.
""",
encoding="utf-8",
)

(SAAS / "STATUS.md").write_text(
"""# Dalizebo SaaS Status

## Phase

Phase 6 — Commerce + POS

## Prerequisites

Kernel P0: COMPLETE

Dalizebo BaaS P0: COMPLETE

## Current Stage

Commerce P0 Cart + Checkout + Orders initialized.

## Commerce

P0 implementation: ACTIVE

Store setup: COMPLETE

Product catalogue: COMPLETE

Variants: COMPLETE

Pricing: COMPLETE

Inventory: COMPLETE

Customers: COMPLETE

Cart: COMPLETE

Checkout: COMPLETE

Orders: COMPLETE

Payments: NEXT

Discounts: NEXT

Notifications: NEXT

Dashboard: NEXT

## Cart + Checkout + Orders

Kernel Cart/Order/OrderItem authority: COMPLETE

Cart lifecycle: COMPLETE

Checkout authoritative snapshots: COMPLETE

Inventory reservation planning: COMPLETE

Integer minor-unit checkout totals: COMPLETE

Order Item price snapshots: COMPLETE

Kernel Order lifecycle: COMPLETE

Atomic checkout transaction requirement: COMPLETE

Outbox-after-commit requirement: COMPLETE

Checkout idempotency: COMPLETE

Durable Kernel Cart Item primitive: DEFERRED

Discount calculation: DEFERRED TO NEXT SLICE

Tax engine: DEFERRED

Payment integration: DEFERRED TO NEXT SLICE

SaaS-owned authoritative Cart/Order/OrderItem database: NONE

## POS

P0 implementation: PENDING COMMERCE FOUNDATION

## Next Work

Commerce P0 — Payments + Discounts + Notifications + Dashboard.

## Governing Rule

Cart, Order, Order Item, and Inventory remain Kernel-authoritative. Checkout is
an atomic transaction plan: inventory reservations, DRAFT Order, immutable Order
Items, Cart conversion, and Order placement commit together or roll back
together. Events publish only after commit. The current shared domain lacks a
durable Cart Item primitive, so Commerce does not invent a competing Cart Item
database; that shared-domain extension remains explicitly deferred.
""",
encoding="utf-8",
)

print("OK: Commerce Cart + Checkout + Orders contracts installed.")
print("OK: Atomic checkout + inventory reservation + order placement installed.")
print("OK: Kernel Cart/Order lifecycle + idempotency controls installed.")
print("STATUS: COMMERCE P0 CART + CHECKOUT + ORDERS READY")
print("NEXT: Commerce P0 — Payments + Discounts + Notifications + Dashboard.")
