# Commerce P0 — Inventory Contract

## Purpose

Dalizebo Commerce Inventory orchestrates stock operations against the
authoritative Kernel `INVENTORY_ITEM` entity.

Commerce does not own a competing inventory table or hidden stock state.

## Kernel Inventory Invariants

An Inventory Item contains:

- id
- tenant scope
- product_variant_id
- store_id
- branch_id
- quantity_on_hand
- quantity_reserved

Required invariants:

- quantity_on_hand >= 0
- quantity_reserved >= 0
- quantity_reserved <= quantity_on_hand

Available stock is:

`quantity_on_hand - quantity_reserved`

## Authority Evidence

Inventory creation requires exact-tenant Kernel commerce evidence for:

- Product Variant
- Store
- Branch when branch_id is present

Inventory adjustment requires exact-tenant evidence for the existing
Inventory Item.

Evidence is ephemeral validation input and never a SaaS-owned authoritative
copy.

## Inventory Creation

Creation supplies explicit initial quantities and is validated through the
Kernel `InventoryItem` runtime before a platform command is produced.

## Inventory Adjustment

Adjustments are explicit before/after transitions.

Input contains:

- expected_quantity_on_hand
- expected_quantity_reserved
- quantity_on_hand_delta
- quantity_reserved_delta
- reason
- source_ref

The runtime computes target quantities and validates the resulting Kernel
Inventory Item.

The expected values are forwarded to the persistence adapter as optimistic
concurrency evidence. P0 does not claim the database currently provides a
version column; the adapter must compare authoritative values atomically before
commit.

## Integrity

- no negative inventory
- reserved stock never exceeds on-hand stock
- mutations are idempotent
- tenant evidence fails closed
- no hidden automatic inventory deductions in this slice
- checkout/POS deduction will reuse this same authority later
