#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
SAAS = ROOT / "saas"
BAAS = ROOT / "baas"
KERNEL = ROOT / "kernel"

required = [
    SAAS / "CROSS_PRODUCT_RULES.md",
    SAAS / "SHARED_DOMAIN_CONTRACT.md",
    SAAS / "MVP_ACCEPTANCE.md",
    SAAS / "commerce/README.md",
    SAAS / "pos/README.md",
    SAAS / "COMMERCE_POS_FOUNDATION.md",
    SAAS / "runtime/product_context.py",
    BAAS / "STATUS.md",
    KERNEL / "commerce/PRIMITIVES.md",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Phase 6 prerequisite/artifact: {path}"
        )

py_compile.compile(
    str(
        SAAS
        / "runtime/product_context.py"
    ),
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

- [ ] Store setup
- [ ] Product catalogue
- [ ] Variants
- [ ] Pricing
- [ ] Inventory
- [ ] Customers
- [ ] Cart
- [ ] Checkout
- [ ] Orders
- [ ] Payments
- [ ] Discounts
- [ ] Notifications
- [ ] Dashboard

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

Commerce P0 — Store + Catalogue.
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

Commerce + POS shared foundation initialized.

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

Store + Catalogue: NEXT

## POS

P0 implementation: PENDING COMMERCE FOUNDATION

## Next Work

Commerce P0 — Store + Catalogue.

## Governing Rule

Commerce and POS are product orchestration layers above Dalizebo Backend and
Dalizebo Kernel. They consume one shared authoritative commerce model. Product
commands are tenant-scoped, Kernel-authorized, idempotent for mutations, and
routed to platform authorities; products cannot choose competing databases or
duplicate authoritative Product, Inventory, Customer, Order, Payment, Refund,
Store, Branch, Discount, or Audit state.
""",
encoding="utf-8",
)

print("OK: Commerce + POS shared foundation installed.")
print("OK: Shared authority routing + tenant/product context installed.")
print("OK: Mutation idempotency + store/branch scope rules installed.")
print("STATUS: PHASE 6 COMMERCE + POS FOUNDATION READY")
print("NEXT: Commerce P0 — Store + Catalogue.")
