# Dalizebo SaaS Status

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
