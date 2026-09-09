# POS P0 — Product Search Contract

## Modes

- TEXT
- SKU
- BARCODE

## TEXT

Searches active Product / active Variant projection using a bounded query.

- length: 2..128
- tenant/store/branch scoped
- optional available-only filter
- limit: 1..100

## SKU

Exact organization-scoped Variant SKU lookup.

SKU values are preserved as identifiers and may not be blank.

## BARCODE

Exact organization-scoped Variant barcode lookup using the canonical Kernel
barcode extension introduced by migration:

`0003_kernel_product_variant_barcode.sql`

Barcode values:

- 3..128 characters
- safe identifier characters only
- unique per Organization when present

## Inventory Scope

POS search joins branch inventory using:

- organization_id
- product_variant_id
- store_id
- branch_id

The read adapter exposes quantity metadata only from authoritative Kernel
Inventory Items.

## State

`READY_FOR_POS_PRODUCT_SEARCH_ADAPTER`

The search plan is read-only and never becomes an authoritative product index.
A future search accelerator may cache/projection-index results but cannot own
Product/Variant truth.
