# Commerce P0 — Discounts Contract

## Purpose

Dalizebo Commerce Discounts orchestrates the shared Kernel `DISCOUNT` primitive
and deterministic checkout discount quotes.

Commerce does not create a competing discount authority.

## Supported P0 Discounts

Kernel types:

- FIXED
- PERCENTAGE

FIXED:

- value_minor > 0
- currency required
- basis_points forbidden

PERCENTAGE:

- basis_points 1..10000
- value_minor forbidden

## Quote

P0 applies one discount per checkout quote.

Percentage calculation is deterministic integer arithmetic:

`discount_minor = floor(subtotal_minor × basis_points / 10000)`

Fixed discounts are capped by the checkout subtotal.

A discount may never make the checkout total negative.

## Checkout Integration

The existing Cart + Checkout + Orders slice uses `discount_minor = 0` by
default.

This slice provides a `CheckoutDiscountOverlay` that must be applied before the
checkout transaction is executed. It overrides the DRAFT Order money fields:

- subtotal_minor
- discount_minor
- tax_minor
- total_minor

The underlying Order remains Kernel-authoritative.

Tax remains zero in P0 unless a future shared tax contract explicitly supplies
a tax value.

## Integrity

- Kernel Discount validation is mandatory
- currency mismatch fails closed
- mutation commands are idempotent
- no hidden repricing after Order placement
