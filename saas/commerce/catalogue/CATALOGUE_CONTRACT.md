# Commerce P0 — Catalogue Contract

## Purpose

Dalizebo Commerce Catalogue orchestrates Product, Product Variant, and Pricing
operations against the shared Kernel commerce model.

Commerce does not persist competing authoritative Product or Variant records.

## Kernel Model

Kernel owns:

### Product

- id
- tenant scope
- name
- description
- status
- created_at
- updated_at

Statuses:

- DRAFT
- ACTIVE
- ARCHIVED

Product lifecycle:

- DRAFT → ACTIVE
- DRAFT → ARCHIVED
- ACTIVE → ARCHIVED
- ARCHIVED is terminal in P0

### Product Variant

- id
- tenant scope
- product_id
- sku
- price_minor
- currency
- active
- created_at
- updated_at

Kernel/DB invariants include:

- price is integer minor units
- price >= 0
- currency is a three-letter uppercase code
- SKU is required
- SKU uniqueness is enforced per Organization by authoritative persistence

## Pricing

Pricing in this slice is the Variant price already owned by Kernel.

Commerce supports:

- initial Variant price
- Variant price update

It does not introduce a separate price table or price authority.

Future price books/promotions may extend the platform only through an explicit
shared-domain decision.

## Authority Evidence

Operations against an existing Product, Variant, or Store require ephemeral
Kernel authority evidence:

- source = `kernel.commerce`
- entity type
- entity ID
- exact tenant scope

Evidence is validation input, not a SaaS-owned copy of authoritative state.

This requirement also compensates at the product boundary for the current
database hardening gap where some commerce foreign keys are global IDs rather
than composite tenant foreign keys.

## Execution

Every mutation becomes a Phase 6 `ProductCommand`.

Authority routing is derived by the shared foundation. Product code cannot
choose a database or bypass Kernel/BaaS authority.

## No Duplicate Models

Commerce may own presentation state and workflow state.

It may not own a competing authoritative copy of:

- Store
- Product
- Product Variant
- Inventory
- Customer
- Cart
- Order
- Payment
- Refund
- Discount
