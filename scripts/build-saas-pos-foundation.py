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
    SAAS / "COMMERCE_POS_FOUNDATION.md",
    SAAS / "runtime/product_context.py",
    SAAS / "pos/foundation/POS_FOUNDATION_CONTRACT.md",
    SAAS / "pos/catalogue/PRODUCT_SEARCH_CONTRACT.md",
    SAAS / "pos/foundation/runtime.py",
    KERNEL / "authorization/runtime.py",
    KERNEL / "commerce/variant_identifiers.py",
    KERNEL / "migrations/sql/0002_kernel_commerce_primitives.sql",
    KERNEL / "migrations/sql/0003_kernel_product_variant_barcode.sql",
    BAAS / "auth/AUTH_CONTRACT.md",
    BAAS / "auth/runtime.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing POS foundation prerequisite/artifact: {path}"
        )

for path in [
    SAAS / "runtime/product_context.py",
    SAAS / "pos/foundation/runtime.py",
    KERNEL / "authorization/runtime.py",
    KERNEL / "commerce/variant_identifiers.py",
    BAAS / "auth/runtime.py",
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

## Commerce P0 Result

DALIZEBO COMMERCE P0: COMPLETE

## POS P0

- [x] Branches
- [x] Staff
- [x] Roles
- [x] Product search
- [x] Barcode and SKU lookup
- [ ] Cart
- [ ] Checkout
- [ ] Cash payment recording
- [ ] Card payment recording
- [ ] Receipts
- [ ] Inventory deduction
- [ ] Returns
- [ ] Daily summaries

## POS Branch Components

- [x] Kernel Branch authority boundary
- [x] Exact-tenant ACTIVE Store prerequisite
- [x] Branch creation
- [x] Branch ACTIVE/INACTIVE lifecycle
- [x] POS store/branch execution context

## POS Staff + Roles Components

- [x] BaaS HUMAN_USER identity prerequisite
- [x] No duplicate POS User authority
- [x] Kernel PermissionDefinition authority
- [x] Kernel RoleDefinition authority
- [x] POS P0 permission catalogue
- [x] Tenant-scoped Kernel roles
- [x] Branch-scoped staff assignment relationship
- [x] Staff role change
- [x] Staff deactivation
- [x] Disabled identity rejection
- [x] Cross-scope staff assignment rejection
- [ ] Durable production POS staff-assignment adapter

## POS Product Search Components

- [x] Branch-scoped active product search
- [x] Exact SKU lookup
- [x] Shared canonical Product Variant barcode extension
- [x] Exact barcode lookup
- [x] Organization barcode uniqueness
- [x] Branch inventory source scope
- [x] Bounded read plan
- [x] No POS-owned Product search authority

## Current Next Work

POS P0 — Cart + Checkout + Payments + Receipts.
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

POS P0 Branches + Staff + Roles + Product Search initialized.

## POS

Branches: COMPLETE

Staff: COMPLETE (P0 control-plane assignment)

Roles: COMPLETE

Product search: COMPLETE

Barcode and SKU lookup: COMPLETE

Cart: NEXT

Checkout: NEXT

Cash payment recording: NEXT

Card payment recording: NEXT

Receipts: NEXT

Inventory deduction: PENDING

Returns: PENDING

Daily summaries: PENDING

## Branches

Kernel Branch authority: COMPLETE

ACTIVE Store prerequisite: COMPLETE

Branch lifecycle: COMPLETE

## Staff + Roles

BaaS HUMAN_USER identity boundary: COMPLETE

Kernel RBAC authority: COMPLETE

POS permission catalogue: COMPLETE

Branch staff assignment: COMPLETE

Durable production staff-assignment adapter: DEFERRED

## Product Search

Branch-scoped read plan: COMPLETE

SKU lookup: COMPLETE

Canonical Kernel Variant barcode field: COMPLETE

Barcode lookup: COMPLETE

POS-owned Product/Variant search authority: NONE

## Next Work

POS P0 — Cart + Checkout + Payments + Receipts.

## Governing Rule

POS reuses shared Branch, User, Role, Product, Product Variant, and Inventory
authority. Staff assignments bind an existing BaaS HUMAN_USER identity to an
existing Kernel role and branch without creating a second identity or RBAC
system. Product lookup is branch-scoped and read-only. Barcode is implemented as
a shared nullable Product Variant identifier with organization uniqueness, not
as a POS-owned mapping table.
""",
encoding="utf-8",
)

print("OK: POS Branch + Staff + Roles + Product Search installed.")
print("OK: BaaS identity + Kernel RBAC authority boundaries installed.")
print("OK: Shared Variant barcode migration + SKU/barcode lookup installed.")
print("STATUS: POS P0 BRANCHES + STAFF + ROLES + PRODUCT SEARCH READY")
print("NEXT: POS P0 — Cart + Checkout + Payments + Receipts.")
