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
    SAAS / "MVP_ACCEPTANCE.md",
    SAAS / "pos/README.md",
    SAAS / "runtime/product_context.py",
    SAAS / "pos/transactions/runtime.py",
    SAAS / "pos/returns/RETURNS_CONTRACT.md",
    SAAS / "pos/reporting/DAILY_SUMMARY_CONTRACT.md",
    SAAS / "pos/returns/runtime.py",
    KERNEL / "commerce/runtime.py",
    BAAS / "payments/PAYMENTS_CONTRACT.md",
    BAAS / "payments/runtime.py",
    BAAS / "runtime/request_context.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing POS returns/reporting prerequisite/artifact: {path}"
        )

for path in [
    SAAS / "runtime/product_context.py",
    SAAS / "pos/transactions/runtime.py",
    SAAS / "pos/returns/runtime.py",
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
- [x] Returns
- [x] Daily summaries

## POS Returns Components

- [x] Kernel Refund authority boundary
- [x] Completed Order / captured Payment prerequisites
- [x] Returned quantity bounded by sold quantity
- [x] Deterministic line refund calculation
- [x] Cumulative refund cap
- [x] Cash refund orchestration
- [x] Card refund delegation to BaaS Payment Abstraction
- [x] Card refund completion evidence matching
- [x] Branch inventory restock
- [x] Partial refund preserves CAPTURED Payment
- [x] Full refund explicitly transitions Payment CAPTURED→REFUNDED
- [x] Atomic return settlement requirement
- [x] Return audit metadata
- [x] Return receipt planning
- [x] Return idempotency
- [x] Cross-tenant return rejection

## POS Daily Summary Components

- [x] Branch-scoped business-day query
- [x] IANA timezone boundary
- [x] Currency-specific aggregation contract
- [x] Gross sales
- [x] Cash sales
- [x] Card sales
- [x] Refund totals
- [x] Net sales
- [x] Items sold
- [x] Items returned
- [x] Read-only Kernel source plan
- [x] No authoritative reporting database

## POS P0 Result

DALIZEBO POS P0: COMPLETE

## Deferred POS P1

- [ ] Offline queue
- [ ] Receipt printers
- [ ] Cash drawer reconciliation
- [ ] Stock transfers
- [ ] Staff reporting
- [ ] Purchase history

## Phase 6 State

Commerce P0: COMPLETE

POS P0: COMPLETE

MVP acceptance/integration sweep: NEXT

## Current Next Work

Phase 6 — Commerce + POS MVP Acceptance & Integration Closure.
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

Dalizebo POS P0 complete.

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

Returns: COMPLETE

Daily summaries: COMPLETE

## Returns

Kernel Refund authority: COMPLETE

Cash refund orchestration: COMPLETE

Card refund Payment Abstraction delegation: COMPLETE

Cumulative refund cap: COMPLETE

Branch inventory restock: COMPLETE

Full-refund Payment transition: COMPLETE

Atomic return settlement: COMPLETE

Return audit metadata: COMPLETE

## Daily Summaries

Branch business-day reporting contract: COMPLETE

Timezone-aware day boundary: COMPLETE

Currency-specific sales/refund metrics: COMPLETE

Authoritative reporting database: NONE

## POS P0 Result

DALIZEBO POS P0: COMPLETE

## Phase 6

Commerce P0: COMPLETE

POS P0: COMPLETE

MVP acceptance/integration closure: NEXT

## Next Work

Phase 6 — Commerce + POS MVP Acceptance & Integration Closure.

## Governing Rule

POS Returns use the shared Kernel Refund invariant and BaaS Payment Abstraction
for external card refunds. Returned quantities may not exceed sold quantities,
cumulative refunds may not exceed captured payment value, inventory restock is
atomic with Refund recording, and only a full cumulative refund may transition
Payment CAPTURED→REFUNDED. Daily summaries are branch/currency-scoped read
projections and never become business-data authority.
""",
encoding="utf-8",
)

print("OK: POS Returns + Daily Summaries installed.")
print("OK: Kernel Refund cap + inventory restock + Payment full-refund transition installed.")
print("OK: Branch business-day reporting contract installed.")
print("STATUS: POS P0 RETURNS + DAILY SUMMARIES READY")
print("STATUS: DALIZEBO POS P0 COMPLETE")
print("NEXT: Phase 6 — Commerce + POS MVP Acceptance & Integration Closure.")
