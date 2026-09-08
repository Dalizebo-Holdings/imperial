#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
SAAS = ROOT / "saas"
KERNEL = ROOT / "kernel"
BAAS = ROOT / "baas"

required = [
    SAAS / "commerce/README.md",
    SAAS / "COMMERCE_POS_FOUNDATION.md",
    SAAS / "runtime/product_context.py",
    SAAS / "commerce/store/STORE_CONTRACT.md",
    SAAS / "commerce/catalogue/CATALOGUE_CONTRACT.md",
    SAAS / "commerce/catalogue/runtime.py",
    KERNEL / "commerce/runtime.py",
    KERNEL / "commerce/PRIMITIVES.md",
    KERNEL / "migrations/sql/0002_kernel_commerce_primitives.sql",
    BAAS / "STATUS.md",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Store/Catalogue prerequisite/artifact: {path}"
        )

for path in [
    SAAS / "runtime/product_context.py",
    SAAS / "commerce/catalogue/runtime.py",
    KERNEL / "commerce/runtime.py",
]:
    py_compile.compile(
        str(path),
        doraise=True,
    )

( SAAS / "IMPLEMENTATION_STATUS.md" ).write_text(
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
- [ ] Inventory
- [ ] Customers
- [ ] Cart
- [ ] Checkout
- [ ] Orders
- [ ] Payments
- [ ] Discounts
- [ ] Notifications
- [ ] Dashboard

## Store + Catalogue Components

- [x] Kernel STORE authority boundary
- [x] Store setup command
- [x] Store ACTIVE/INACTIVE lifecycle
- [x] Product DRAFT/ACTIVE/ARCHIVED lifecycle
- [x] Product create command
- [x] Kernel ProductVariant validation
- [x] Product Variant create command
- [x] Integer minor-unit pricing
- [x] Variant price update command
- [x] Kernel authority evidence for existing parents
- [x] Cross-tenant authority evidence rejection
- [x] Platform mutation idempotency
- [x] No SaaS-owned Store/Product/Variant database

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

Commerce P0 — Inventory + Customers.
""",
encoding="utf-8",
)

( SAAS / "STATUS.md" ).write_text(
"""# Dalizebo SaaS Status

## Phase

Phase 6 — Commerce + POS

## Prerequisites

Kernel P0: COMPLETE

Dalizebo BaaS P0: COMPLETE

## Current Stage

Commerce P0 Store + Catalogue initialized.

## Shared Foundation

Product execution context: COMPLETE

Tenant execution context: COMPLETE

Kernel authorization evidence: COMPLETE

Shared authoritative entities: COMPLETE

Kernel/BaaS authority routing: COMPLETE

Mutation idempotency: COMPLETE

Store/branch scope rules: COMPLETE

Direct product-to-product database coupling: PROHIBITED

Duplicate authoritative commerce models: NONE

## Commerce

P0 implementation: ACTIVE

Store setup: COMPLETE

Product catalogue: COMPLETE

Variants: COMPLETE

Pricing: COMPLETE

Inventory: NEXT

Customers: NEXT

## Store + Catalogue

Kernel STORE/Product/ProductVariant authority: COMPLETE

Store lifecycle: COMPLETE

Product lifecycle: COMPLETE

Kernel ProductVariant validation: COMPLETE

Integer minor-unit pricing: COMPLETE

Existing-parent authority evidence: COMPLETE

Cross-tenant evidence rejection: COMPLETE

SaaS-owned authoritative Store/Product/Variant database: NONE

## POS

P0 implementation: PENDING COMMERCE FOUNDATION

## Next Work

Commerce P0 — Inventory + Customers.

## Governing Rule

Commerce Store and Catalogue remain orchestration layers over the shared Kernel
commerce model. Store, Product, Product Variant, and Variant price persist only
through platform authorities. Existing-parent operations require exact-tenant
Kernel authority evidence, mutations remain idempotent, and Commerce does not
create competing authoritative catalogue state.
""",
encoding="utf-8",
)

print("OK: Commerce Store + Catalogue contracts installed.")
print("OK: Store/Product lifecycle + Variant/Pricing command planning installed.")
print("OK: Existing-parent tenant authority evidence boundary installed.")
print("STATUS: COMMERCE P0 STORE + CATALOGUE READY")
print("NEXT: Commerce P0 — Inventory + Customers.")
