# Commerce P0 — Cart + Checkout Contract

## Purpose

Dalizebo Commerce Cart and Checkout orchestrate the shared Kernel `CART`,
`ORDER`, `ORDER_ITEM`, and `INVENTORY_ITEM` authorities.

Commerce does not create competing authoritative Cart, Order, Order Item, or
Inventory stores.

## Cart P0

Kernel owns the Cart record:

- id
- tenant scope
- store_id
- customer_id
- status
- currency
- timestamps

Kernel Cart states:

- OPEN
- CONVERTED
- ABANDONED

Only `OPEN` may transition, and only to:

- CONVERTED
- ABANDONED

Commerce P0 supports:

- Cart creation
- Cart abandonment
- Cart conversion as part of checkout

## Cart Line Boundary

The current shared Kernel model does not contain a durable `CART_ITEM`
primitive/table.

P0 therefore does not invent a SaaS-owned authoritative Cart Item database.

Checkout receives an authoritative line snapshot from the platform adapter.
That snapshot contains Product/Variant/Inventory identity, current price, and
inventory quantities needed to validate checkout.

Durable cross-session Cart Item persistence remains deferred until the shared
Kernel domain explicitly adds a canonical Cart Item primitive.

## Checkout

Checkout input includes:

- checkout_id
- cart_id
- order_id
- store_id
- optional customer_id
- currency
- line snapshots
- idempotency_key
- requested_at

Each line snapshot contains:

- order_item_id
- product_id
- product_variant_id
- inventory_item_id
- quantity
- unit_price_minor
- currency
- expected_quantity_on_hand
- expected_quantity_reserved
- Kernel commerce snapshot reference

## Pricing

P0 checkout uses the authoritative Variant price snapshot.

Rules:

- integer minor units only
- quantity > 0
- all line currencies equal checkout currency
- subtotal = sum(quantity × unit_price_minor)
- discount_minor = 0 in this slice
- tax_minor = 0 in this slice
- total_minor = subtotal_minor

Discount calculation is implemented in the next Commerce slice.

Tax engine integration is deferred and P0 does not fabricate tax decisions.

## Inventory Reservation

Checkout reserves inventory explicitly.

For each line:

- target on-hand remains unchanged
- target reserved = expected reserved + checkout quantity
- Kernel InventoryItem invariants must still hold

The persistence adapter must atomically compare expected quantities before
applying the reservation.

No hidden inventory deduction occurs.

## Atomic Checkout Transaction

Checkout emits a composite transaction plan:

1. reserve each Inventory Item
2. create Order in DRAFT
3. create immutable Order Item price snapshots
4. convert Cart OPEN → CONVERTED
5. transition Order DRAFT → PLACED
6. publish audit/domain events only after commit

Requirement:

`KERNEL_ATOMIC_TRANSACTION`

If any command fails, the transaction must roll back all state mutations.

## Idempotency

The checkout transaction has a deterministic transaction ID.

Same checkout idempotency scope + same canonical request returns the same
transaction identity.

Same idempotency key + different checkout material fails closed.
