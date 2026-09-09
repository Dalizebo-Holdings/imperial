# Dalizebo SaaS Status

## Phase

Phase 6 — Commerce + POS

## Prerequisites

Kernel P0: COMPLETE

Dalizebo BaaS P0: COMPLETE

Dalizebo Commerce P0: COMPLETE

## Current Stage

POS P0 Cart + Checkout + Payments + Receipts initialized.

## POS

Branches: COMPLETE

Staff: COMPLETE

Roles: COMPLETE

Product search: COMPLETE

Barcode and SKU lookup: COMPLETE

Cart: COMPLETE

Checkout: COMPLETE

Cash payment recording: COMPLETE

Card payment recording: COMPLETE

Receipts: COMPLETE

Inventory deduction: COMPLETE

Returns: NEXT

Daily summaries: NEXT

## Cart + Checkout

Kernel Cart/Order/OrderItem authority: COMPLETE

Branch-scoped transient cart lines: COMPLETE

Durable Kernel Cart Item primitive: DEFERRED

Inventory reservation: COMPLETE

Atomic checkout transaction: COMPLETE

## Payments

Cash settlement: COMPLETE

Explicit cash Payment lifecycle: COMPLETE

Card Payment Abstraction delegation: COMPLETE

Explicit card Payment lifecycle: COMPLETE

Inventory deduction after successful settlement: COMPLETE

Order completion after successful settlement: COMPLETE

Split tender: DEFERRED

Cash drawer reconciliation: DEFERRED TO P1

## Receipts

Deterministic receipt plan: COMPLETE

Post-commit rendering boundary: COMPLETE

Physical receipt-printer adapter: DEFERRED TO P1

## Next Work

POS P0 — Returns + Daily Summaries.

## Governing Rule

POS transactions reuse shared Kernel Cart, Inventory, Order, Order Item, and
Payment authority. Checkout reserves branch inventory and places the Order.
Successful cash/card settlement explicitly captures Payment, converts the
reservation into sold inventory, completes the Order, and only then enables
receipt rendering. Card provider work stays behind BaaS Payment Abstraction.
The current shared domain still lacks durable Cart Item persistence, so POS uses
transient session lines rather than creating a competing authoritative table.
