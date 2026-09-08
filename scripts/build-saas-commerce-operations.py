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
    SAAS / "commerce/README.md",
    SAAS / "runtime/product_context.py",
    SAAS / "commerce/checkout/runtime.py",
    SAAS / "commerce/payments/PAYMENTS_CONTRACT.md",
    SAAS / "commerce/discounts/DISCOUNTS_CONTRACT.md",
    SAAS / "commerce/notifications/NOTIFICATIONS_CONTRACT.md",
    SAAS / "commerce/dashboard/DASHBOARD_CONTRACT.md",
    SAAS / "commerce/operations/runtime.py",
    KERNEL / "commerce/runtime.py",
    BAAS / "payments/PAYMENTS_CONTRACT.md",
    BAAS / "payments/runtime.py",
    BAAS / "events/README.md",
    BAAS / "webhooks/README.md",
    BAAS / "runtime/request_context.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Commerce completion prerequisite/artifact: {path}"
        )

for path in [
    SAAS / "runtime/product_context.py",
    SAAS / "commerce/checkout/runtime.py",
    SAAS / "commerce/operations/runtime.py",
    KERNEL / "commerce/runtime.py",
    BAAS / "payments/runtime.py",
    BAAS / "runtime/request_context.py",
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
- [x] Payments
- [x] Discounts
- [x] Notifications
- [x] Dashboard

## Payments Components

- [x] BaaS Payment Abstraction delegation
- [x] Kernel Payment authority boundary
- [x] Order PLACED payment-start gate
- [x] Idempotent provider-neutral payment plan
- [x] Shared PENDING Payment creation command
- [x] Explicit payment transition commands
- [x] CAPTURED payment → Order confirmation plan
- [x] No raw payment/provider credentials in Commerce metadata
- [x] No hidden payment transitions

## Discounts Components

- [x] Kernel Discount validation
- [x] FIXED discount support
- [x] PERCENTAGE basis-points support
- [x] Deterministic integer discount quote
- [x] Discount may not make total negative
- [x] Checkout DRAFT Order discount overlay
- [x] No hidden repricing after Order placement

## Notifications Components

- [x] Post-commit notification intent
- [x] BaaS Events/Webhooks boundary
- [x] WEBHOOK channel
- [x] INTERNAL channel
- [x] Opaque recipient references
- [x] Notification idempotency
- [x] Duplicate-delivery-safe contract
- [ ] Email delivery adapter (BaaS P1)

## Dashboard Components

- [x] Tenant/store scoped read plan
- [x] Time-bounded query contract
- [x] Currency-specific money aggregation contract
- [x] Orders/payments/customers/inventory source plan
- [x] No Dashboard authoritative database
- [ ] Durable analytics/read-model accelerator

## Commerce P0 Result

DALIZEBO COMMERCE P0: COMPLETE

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

POS P0 — Branches + Staff + Roles + Product Search.
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

Dalizebo Commerce P0 complete.

## Commerce

Store setup: COMPLETE

Product catalogue: COMPLETE

Variants: COMPLETE

Pricing: COMPLETE

Inventory: COMPLETE

Customers: COMPLETE

Cart: COMPLETE

Checkout: COMPLETE

Orders: COMPLETE

Payments: COMPLETE

Discounts: COMPLETE

Notifications: COMPLETE (event-driven P0)

Dashboard: COMPLETE (read-contract P0)

## Payments

BaaS Payment Abstraction delegation: COMPLETE

Explicit Kernel Payment transitions: COMPLETE

CAPTURED → Order confirmation orchestration: COMPLETE

Direct provider execution from Commerce: NONE

## Discounts

Kernel Discount validation: COMPLETE

Deterministic FIXED/PERCENTAGE quoting: COMPLETE

Checkout pre-execution discount overlay: COMPLETE

Hidden repricing after Order placement: NONE

## Notifications

Post-commit Events/Webhooks intent: COMPLETE

Email delivery: DEFERRED TO BAAS P1

## Dashboard

Scoped dashboard read contract: COMPLETE

Authoritative Dashboard database: NONE

Durable analytics/read-model accelerator: DEFERRED

## Commerce P0 Result

DALIZEBO COMMERCE P0: COMPLETE

## POS

P0 implementation: ACTIVE NEXT

## Next Work

POS P0 — Branches + Staff + Roles + Product Search.

## Governing Rule

Commerce remains an orchestration product over Kernel/BaaS authority. Payment
provider work stays behind Payment Abstraction; payment lifecycle edges remain
explicit. Discounts are Kernel-validated and applied before checkout execution.
Notifications publish only after commit through Events/Webhooks. Dashboard is a
scoped read projection, never an authoritative business-data store.
""",
encoding="utf-8",
)

print("OK: Commerce Payments + Discounts + Notifications + Dashboard installed.")
print("OK: Payment Abstraction + Kernel transition boundary installed.")
print("OK: Kernel Discounts + post-commit notifications + dashboard read plan installed.")
print("STATUS: COMMERCE P0 OPERATIONS READY")
print("STATUS: DALIZEBO COMMERCE P0 COMPLETE")
print("NEXT: POS P0 — Branches + Staff + Roles + Product Search.")
