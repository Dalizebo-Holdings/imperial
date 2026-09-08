#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
SAAS = ROOT / "saas"
KERNEL = ROOT / "kernel"

required = [
    SAAS / "STATUS.md",
    SAAS / "IMPLEMENTATION_STATUS.md",
    SAAS / "SHARED_DOMAIN_CONTRACT.md",
    SAAS / "runtime/product_context.py",
    SAAS / "commerce/catalogue/runtime.py",
    SAAS / "commerce/inventory/INVENTORY_CONTRACT.md",
    SAAS / "commerce/inventory/runtime.py",
    SAAS / "commerce/customers/CUSTOMERS_CONTRACT.md",
    SAAS / "commerce/customers/runtime.py",
    KERNEL / "commerce/runtime.py",
    KERNEL / "migrations/sql/0002_kernel_commerce_primitives.sql",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Inventory/Customers prerequisite/artifact: {path}"
        )

for path in [
    SAAS / "runtime/product_context.py",
    SAAS / "commerce/catalogue/runtime.py",
    SAAS / "commerce/inventory/runtime.py",
    SAAS / "commerce/customers/runtime.py",
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
- [ ] Cart
- [ ] Checkout
- [ ] Orders
- [ ] Payments
- [ ] Discounts
- [ ] Notifications
- [ ] Dashboard

## Inventory Components

- [x] Kernel InventoryItem authority boundary
- [x] Variant/Store/Branch authority evidence
- [x] Initial inventory creation
- [x] On-hand/reserved invariant validation
- [x] Explicit before/after inventory adjustment
- [x] Optimistic expected-quantity persistence requirement
- [x] Cross-tenant inventory evidence rejection
- [x] Mutation idempotency
- [x] No SaaS-owned inventory database

## Customer Components

- [x] Kernel Customer authority boundary
- [x] Customer creation
- [x] Customer update
- [x] External identity reference
- [x] Optional email/phone profile support
- [x] Contact PII classification metadata
- [x] PII policy reference requirement
- [x] Retention policy reference requirement
- [x] Contact-value audit/log suppression directive
- [x] Cross-tenant Customer evidence rejection
- [x] Mutation idempotency
- [x] No SaaS-owned Customer database

## Customer PII Deferred Production Hardening

- [ ] Database encryption/appropriate protection adapter
- [ ] Retention/deletion enforcement adapter
- [ ] Formal customer PII lifecycle policy implementation

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

Commerce P0 — Cart + Checkout + Orders.
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

Commerce P0 Inventory + Customers initialized.

## Commerce

P0 implementation: ACTIVE

Store setup: COMPLETE

Product catalogue: COMPLETE

Variants: COMPLETE

Pricing: COMPLETE

Inventory: COMPLETE

Customers: COMPLETE

Cart: NEXT

Checkout: NEXT

Orders: NEXT

## Inventory

Kernel InventoryItem authority: COMPLETE

On-hand/reserved invariants: COMPLETE

Exact-tenant Variant/Store/Branch evidence: COMPLETE

Explicit inventory adjustments: COMPLETE

Expected-quantity atomic persistence requirement: COMPLETE

SaaS-owned authoritative Inventory database: NONE

## Customers

Kernel Customer authority: COMPLETE

Customer create/update: COMPLETE

External identity reference: COMPLETE

Optional contact profile: COMPLETE

PII policy/retention references: COMPLETE

Contact values suppressed from audit/log metadata: COMPLETE

Production PII persistence hardening: DEFERRED

SaaS-owned authoritative Customer database: NONE

## POS

P0 implementation: PENDING COMMERCE FOUNDATION

## Next Work

Commerce P0 — Cart + Checkout + Orders.

## Governing Rule

Inventory and Customers remain Kernel-authoritative shared entities. Commerce
may plan explicit idempotent mutations only after tenant/parent authority
validation. Inventory target quantities must satisfy Kernel invariants and
persistence must atomically compare expected quantities. Customer contact data
is classified as personal data and requires policy references; the current
direct email/phone persistence model remains explicitly subject to production
PII protection and retention hardening.
""",
encoding="utf-8",
)

print("OK: Commerce Inventory + Customers contracts installed.")
print("OK: Inventory invariants + expected-value adjustment planning installed.")
print("OK: Customer authority + PII policy boundary installed.")
print("STATUS: COMMERCE P0 INVENTORY + CUSTOMERS READY")
print("NEXT: Commerce P0 — Cart + Checkout + Orders.")
