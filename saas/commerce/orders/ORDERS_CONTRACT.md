# Commerce P0 — Orders Contract

## Purpose

Dalizebo Commerce Orders orchestrates the authoritative Kernel `ORDER` and
`ORDER_ITEM` entities.

## Kernel Order Lifecycle

- DRAFT → PLACED
- DRAFT → CANCELLED
- PLACED → CONFIRMED
- PLACED → CANCELLED
- CONFIRMED → COMPLETED
- CONFIRMED → CANCELLED
- COMPLETED terminal
- CANCELLED terminal

All lifecycle validation is delegated to Kernel `OrderState`.

## Order Money

Order creation stores:

- subtotal_minor
- discount_minor
- tax_minor
- total_minor
- currency

P0 Cart + Checkout uses:

- discount_minor = 0
- tax_minor = 0
- total_minor = subtotal_minor

Later Commerce slices may extend these calculations through explicit shared
contracts; they may not mutate order totals invisibly.

## Order Items

Each Order Item is an immutable checkout price snapshot containing:

- product_id
- product_variant_id
- quantity
- unit_price_minor
- total_minor
- currency

Line total invariant:

`total_minor = quantity × unit_price_minor`

## Authority Evidence

Existing Cart, Store, Customer, Inventory Item, Product, Product Variant, and
Order operations require exact-tenant Kernel commerce evidence/snapshots.

This product-layer evidence requirement remains in force until database tenant
integrity hardening is complete.

## Events

Order creation/transition commands carry correlation and audit metadata through
the Phase 6 platform command boundary.

Domain events remain post-commit through the existing Kernel outbox / BaaS
Events path.
