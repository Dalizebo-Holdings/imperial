# POS P0 — Returns Contract

## Purpose

Dalizebo POS Returns records branch-scoped returns against shared Kernel
Order, Payment, Refund, Product Variant, and Inventory Item authority.

POS does not create a competing Refund or Inventory authority.

## Preconditions

A return requires:

- product = POS
- Store + Branch context
- `pos.return.execute`
- Order status = COMPLETED
- Payment status = CAPTURED
- exact-tenant Order + Payment evidence
- returned line snapshots from the completed sale
- refund amount matching returned line value
- cumulative refund <= captured amount

## Return Lines

Each return line contains:

- return_line_id
- order_item_id
- product_id
- product_variant_id
- inventory_item_id
- sold_quantity
- previously_returned_quantity
- return_quantity
- unit_price_minor
- currency
- current inventory on-hand/reserved
- exact Kernel evidence

Rules:

- return_quantity > 0
- previously_returned_quantity >= 0
- previously_returned + return <= sold_quantity
- line refund = return_quantity × unit_price_minor
- all lines use one currency

## Kernel Refund

The shared Kernel `Refund` model remains authoritative.

Validation requires:

- refund_id
- payment_id
- integer minor-unit amount
- currency
- reason
- captured amount
- previously refunded amount

A refund may never exceed captured payment value.

## Cash Return

Cash refund is an internal POS tender workflow.

It creates:

- shared REFUND command
- inventory restock commands
- optional Payment CAPTURED → REFUNDED transition when the cumulative refund
  reaches the entire captured amount
- return receipt metadata

State mutations are one atomic Kernel transaction.

Cash drawer reconciliation remains P1.

## Card Return

Card refunds delegate provider execution to BaaS Payment Abstraction via
`create_refund_plan()`.

The provider plan state is:

`READY_FOR_PROVIDER_REFUND_ADAPTER`

POS does not expose provider credentials.

After an approved BaaS adapter reports successful refund completion, POS may
plan the same Kernel Refund + inventory restock transaction.

The completion evidence is metadata-only and must match:

- refund_id
- payment_id
- provider_id
- provider_reference
- amount_minor
- currency
- approved refund operation reference

## Inventory Restock

Successful return completion adds returned quantity back to branch on-hand
inventory while preserving reserved quantity.

Persistence must atomically compare expected current quantities before update.

## Payment Final State

Partial refund:

- Payment remains CAPTURED
- Refund is a separate authoritative resource

Full cumulative refund:

- explicit Payment CAPTURED → REFUNDED transition

## Audit

Return creation, Refund creation, inventory restock, and full-refund Payment
transition all use the platform command/audit boundary.

Events publish only after commit.

## Idempotency

Return/refund mutations are idempotent.

Same idempotency scope + different return material fails closed.
