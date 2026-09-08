# Dalizebo SaaS Status

## Phase

Phase 6 — Commerce + POS

## Prerequisites

Kernel P0: COMPLETE

Dalizebo BaaS P0: COMPLETE

## Current Stage

Commerce P0 Cart + Checkout + Orders initialized.

## Commerce

P0 implementation: ACTIVE

Store setup: COMPLETE

Product catalogue: COMPLETE

Variants: COMPLETE

Pricing: COMPLETE

Inventory: COMPLETE

Customers: COMPLETE

Cart: COMPLETE

Checkout: COMPLETE

Orders: COMPLETE

Payments: NEXT

Discounts: NEXT

Notifications: NEXT

Dashboard: NEXT

## Cart + Checkout + Orders

Kernel Cart/Order/OrderItem authority: COMPLETE

Cart lifecycle: COMPLETE

Checkout authoritative snapshots: COMPLETE

Inventory reservation planning: COMPLETE

Integer minor-unit checkout totals: COMPLETE

Order Item price snapshots: COMPLETE

Kernel Order lifecycle: COMPLETE

Atomic checkout transaction requirement: COMPLETE

Outbox-after-commit requirement: COMPLETE

Checkout idempotency: COMPLETE

Durable Kernel Cart Item primitive: DEFERRED

Discount calculation: DEFERRED TO NEXT SLICE

Tax engine: DEFERRED

Payment integration: DEFERRED TO NEXT SLICE

SaaS-owned authoritative Cart/Order/OrderItem database: NONE

## POS

P0 implementation: PENDING COMMERCE FOUNDATION

## Next Work

Commerce P0 — Payments + Discounts + Notifications + Dashboard.

## Governing Rule

Cart, Order, Order Item, and Inventory remain Kernel-authoritative. Checkout is
an atomic transaction plan: inventory reservations, DRAFT Order, immutable Order
Items, Cart conversion, and Order placement commit together or roll back
together. Events publish only after commit. The current shared domain lacks a
durable Cart Item primitive, so Commerce does not invent a competing Cart Item
database; that shared-domain extension remains explicitly deferred.
