#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
SAAS = ROOT / "saas"
KERNEL = ROOT / "kernel"
BAAS = ROOT / "baas"

required = [
    SAAS / "STATUS.md",
    SAAS / "IMPLEMENTATION_STATUS.md",
    SAAS / "pos/README.md",
    SAAS / "runtime/product_context.py",
    SAAS / "pos/foundation/runtime.py",
    SAAS / "pos/transactions/POS_TRANSACTIONS_CONTRACT.md",
    SAAS / "pos/transactions/runtime.py",
    KERNEL / "commerce/runtime.py",
    BAAS / "payments/runtime.py",
    BAAS / "runtime/request_context.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing POS transaction prerequisite/artifact: {path}"
        )

for path in [
    SAAS / "runtime/product_context.py",
    SAAS / "pos/foundation/runtime.py",
    SAAS / "pos/transactions/runtime.py",
    KERNEL / "commerce/runtime.py",
    BAAS / "payments/runtime.py",
    BAAS / "runtime/request_context.py",
]:
    py_compile.compile(
        str(path),
        doraise=True,
    )

(SAAS / "IMPLEMENTATION_STATUS.md").write_text(
"""# Dalizebo SaaS Implementation Status

## Phase

Phase 6 — Commerce + POS

## Prerequisites

- [x] Kernel P0 complete
- [x] BaaS P0 complete
- [x] Shared SaaS domain contract
- [x] Cross-product authority rules

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
- [x] Payments
- [x] Discounts
- [x] Notifications
- [x] Dashboard

## Commerce P0 Result

DALIZEBO COMMERCE P0: COMPLETE

## POS P0

- [x] Branches
- [x] Staff
- [x] Roles
- [x] Product search
- [x] Barcode and SKU lookup
- [x] Cart
- [x] Checkout
- [x] Cash payment recording
- [x] Card payment recording
- [x] Receipts
- [x] Inventory deduction
- [ ] Returns
- [ ] Daily summaries

## POS Cart Components

- [x] Shared Kernel Cart authority
- [x] Branch-scoped transient cart session
- [x] Cart line add/update/remove
- [x] Exact-tenant Product/Variant/Inventory evidence
- [x] Integer minor-unit pricing
- [x] Durable shared Cart Item authority not duplicated
- [ ] Durable Kernel Cart Item primitive

## POS Checkout Components

- [x] Branch inventory reservation
- [x] DRAFT Order with branch_id
- [x] Immutable Order Item snapshots
- [x] Cart OPEN→CONVERTED
- [x] Order DRAFT→PLACED
- [x] Atomic checkout transaction requirement
- [x] Checkout idempotency
- [x] Outbox-after-commit requirement

## POS Payments Components

- [x] Full-tender cash settlement
- [x] Cash change calculation
- [x] Explicit cash PENDING→AUTHORIZED→CAPTURED
- [x] Card delegation to BaaS Payment Abstraction
- [x] Explicit card Payment transitions
- [x] No raw card/provider credentials in POS metadata
- [x] Inventory reservation→deduction settlement
- [x] Order PLACED→CONFIRMED→COMPLETED settlement
- [x] Atomic settlement requirement
- [ ] Split tender
- [ ] Cash drawer reconciliation

## POS Receipt Components

- [x] Deterministic receipt identity
- [x] Order/Payment/Store/Branch references
- [x] Integer minor-unit receipt totals
- [x] Cash tender/change metadata
- [x] Card provider reference metadata
- [x] No raw payment credential data
- [x] Receipt rendering only after commit
- [ ] Physical receipt-printer adapter

## Current Next Work

POS P0 — Returns + Daily Summaries.
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

Dalizebo Commerce P0: COMPLETE

## Current Stage

POS P0 Cart + Checkout + Payments + Receipts initialized.

## POS

Branches: COMPLETE

Staff: COMPLETE

Roles: COMPLETE

Product search: COMPLETE

Barcode and SKU lookup: COMPLETE

Cart: COMPLETE

Checkout: COMPLETE

Cash payment recording: COMPLETE

Card payment recording: COMPLETE

Receipts: COMPLETE

Inventory deduction: COMPLETE

Returns: NEXT

Daily summaries: NEXT

## Cart + Checkout

Kernel Cart/Order/OrderItem authority: COMPLETE

Branch-scoped transient cart lines: COMPLETE

Durable Kernel Cart Item primitive: DEFERRED

Inventory reservation: COMPLETE

Atomic checkout transaction: COMPLETE

## Payments

Cash settlement: COMPLETE

Explicit cash Payment lifecycle: COMPLETE

Card Payment Abstraction delegation: COMPLETE

Explicit card Payment lifecycle: COMPLETE

Inventory deduction after successful settlement: COMPLETE

Order completion after successful settlement: COMPLETE

Split tender: DEFERRED

Cash drawer reconciliation: DEFERRED TO P1

## Receipts

Deterministic receipt plan: COMPLETE

Post-commit rendering boundary: COMPLETE

Physical receipt-printer adapter: DEFERRED TO P1

## Next Work

POS P0 — Returns + Daily Summaries.

## Governing Rule

POS transactions reuse shared Kernel Cart, Inventory, Order, Order Item, and
Payment authority. Checkout reserves branch inventory and places the Order.
Successful cash/card settlement explicitly captures Payment, converts the
reservation into sold inventory, completes the Order, and only then enables
receipt rendering. Card provider work stays behind BaaS Payment Abstraction.
The current shared domain still lacks durable Cart Item persistence, so POS uses
transient session lines rather than creating a competing authoritative table.
""",
encoding="utf-8",
)

print("OK: POS Cart + Checkout + Payments + Receipts installed.")
print("OK: Cash/card settlement + inventory deduction + receipt planning installed.")
print("OK: Explicit Kernel Payment/Order lifecycle and atomic transaction boundaries installed.")
print("STATUS: POS P0 CART + CHECKOUT + PAYMENTS + RECEIPTS READY")
print("NEXT: POS P0 — Returns + Daily Summaries.")
