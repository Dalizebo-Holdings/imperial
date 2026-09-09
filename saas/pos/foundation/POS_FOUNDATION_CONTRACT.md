# POS P0 — Branches + Staff + Roles Foundation

## Purpose

Dalizebo POS operates on shared Dalizebo platform authority:

POS
→ Dalizebo Backend
→ Dalizebo Kernel
→ Shared Commerce Primitives

This slice establishes:

- Branch setup and lifecycle
- Staff identity binding
- Branch-scoped POS staff assignments
- Kernel RBAC role definitions
- Product search
- SKU lookup
- Canonical barcode lookup

POS does not create competing User, Role, Store, Branch, Product, Variant, or
Inventory authorities.

## Branch Authority

Branch remains the shared Kernel `BRANCH` entity.

Canonical Branch fields:

- id
- tenant scope
- store_id
- name
- status
- timestamps

Statuses:

- ACTIVE
- INACTIVE

Branch creation requires exact-tenant ACTIVE Store evidence.

Branch status changes are explicit:

- ACTIVE → INACTIVE
- INACTIVE → ACTIVE

## Staff Identity Boundary

A POS staff member is not a second User object.

Staff must reference an existing BaaS Authentication `IdentityRecord`:

- actor_type = HUMAN_USER
- enabled = true
- organization_id must match POS tenant

The staff assignment is a POS-specific relationship:

Identity
+ Kernel Role
+ Store
+ Branch
+ Assignment status

This relationship may be product-specific because it does not duplicate
identity or authorization authority.

P0 keeps the assignment registry in the POS runtime contract. A durable
production assignment adapter remains deferred.

## Roles

Kernel Authorization remains authoritative for permissions and roles.

POS P0 permissions:

- pos.branch.read
- pos.product.read
- pos.cart.create
- pos.cart.update
- pos.checkout.execute
- pos.payment.cash.record
- pos.payment.card.record
- pos.receipt.issue
- pos.inventory.adjust
- pos.return.execute
- pos.summary.read

POS role registration creates/validates canonical Kernel:

- PermissionDefinition
- RoleDefinition

Kernel Role tenant scope remains Organization/Workspace/Project/Environment.

Branch scope is applied by the POS Staff Assignment relationship and by
resource_scope at authorization time.

## Product Search

Operational Product Search requires:

- product=POS
- Store context
- Branch context
- ACTIVE Branch evidence

Read sources:

- kernel.products
- kernel.product_variants
- kernel.inventory_items

Filters always include exact tenant/store/branch scope.

Product must be ACTIVE.
Variant must be active.

## SKU Lookup

SKU is authoritative on `kernel.product_variants` and unique per Organization.

SKU lookup is exact-match.

## Barcode Extension

The existing Kernel P0 Variant schema did not include barcode.

This slice adds a minimal shared Kernel extension:

`kernel.product_variants.barcode text NULL`

with:

- safe canonical identifier validation
- unique `(organization_id, barcode)` when barcode is non-null
- no POS-owned barcode table

Barcode lookup is exact-match.

## Security

- Kernel authorization evidence remains mandatory on product context.
- Cross-tenant Store/Branch evidence fails closed.
- Staff identity must be BaaS-authenticated HUMAN_USER identity metadata.
- Role permissions are restricted to the POS P0 permission catalogue.
- Search queries are bounded.
- No direct product-to-product database coupling is introduced.
