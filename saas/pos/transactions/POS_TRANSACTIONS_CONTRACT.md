# POS P0 — Cart + Checkout + Payments + Receipts

## Purpose

Dalizebo POS transaction flow reuses the same Kernel/BaaS commerce authority as
Dalizebo Commerce while adding branch-scoped in-store tender and receipt
orchestration.

Canonical path:

POS Cart Session
→ Kernel Cart
→ Branch Inventory Reservation
→ Kernel Order + Order Items
→ Cash or Card Settlement
→ Inventory Deduction
→ Order Completion
→ Receipt Rendering

## Authority

Kernel remains authoritative for:

- Cart
- Inventory Item
- Order
- Order Item
- Payment
- Product / Variant pricing
- lifecycle transitions

BaaS Payment Abstraction remains authoritative for provider-neutral card
orchestration.

POS owns only transient branch cart-session state and receipt-rendering metadata.
It does not create competing authoritative commerce records.

## Cart

The current shared Kernel model still has no durable CART_ITEM primitive.

P0 therefore provides a transient POS cart session:

- cart_id
- branch execution scope
- line snapshots
- deterministic line replacement/removal

The authoritative Kernel Cart is still created through the platform command
boundary.

Transient line state must not be treated as durable recovery state.

Durable cross-session Cart Item persistence remains a shared-domain deferred
item.

## Checkout

Checkout requires:

- ACTIVE branch execution context
- `pos.checkout.execute`
- OPEN Cart evidence
- authoritative Product / Product Variant / Inventory evidence
- integer minor-unit prices
- one currency
- available inventory

Atomic checkout transaction:

1. reserve branch inventory
2. create Order DRAFT with branch_id
3. create immutable Order Item price snapshots
4. convert Cart OPEN → CONVERTED
5. transition Order DRAFT → PLACED
6. publish events only after commit

State:

`READY_FOR_KERNEL_TRANSACTION_ADAPTER`

## Cash Payment

Cash settlement requires `pos.payment.cash.record`.

P0 supports full-tender cash sale:

- tendered_minor >= Order total
- payment amount = exact Order total
- change_minor = tendered_minor - Order total
- provider marker = CASH

Kernel Payment lifecycle remains explicit:

`PENDING → AUTHORIZED → CAPTURED`

No hidden direct PENDING → CAPTURED transition is allowed.

Cash drawer reconciliation is P1 and is not claimed here.

## Card Payment

Card settlement requires `pos.payment.card.record`.

POS delegates provider work to BaaS Payment Abstraction.

Commerce/POS never receive provider credentials or raw card data.

Provider result transitions remain explicit:

`PENDING → AUTHORIZED → CAPTURED`

A captured result enables sale settlement.

## Inventory Deduction

Checkout reservation does not deduct on-hand inventory.

Successful settlement atomically converts reservation to sold stock:

- target_on_hand = expected_on_hand - quantity
- target_reserved = expected_reserved_after_checkout - quantity

Kernel InventoryItem validates the final quantities.

Persistence must atomically compare the expected post-checkout quantities.

## Order Completion

Successful full settlement plans:

`PLACED → CONFIRMED → COMPLETED`

using Kernel OrderState.

Payment capture, inventory deduction, and Order completion are one settlement
transaction plan.

## Receipts

Receipt is a product document/projection, not a new commerce authority.

Receipt metadata contains:

- receipt_id
- Order / Payment references
- Store / Branch
- line summaries
- subtotal / discount / tax / total
- tender type
- tendered / change for CASH
- provider reference for CARD when available
- issued_at
- correlation_id

No card PAN/CVV/token/provider credentials may appear.

Receipt state:

`READY_FOR_RECEIPT_RENDERER_AFTER_COMMIT`

Physical receipt-printer integration is P1.

## Idempotency

- Cart creation is idempotent through the product command boundary.
- Checkout transaction identity is deterministic.
- Cash settlement identity is deterministic.
- Card provider planning uses BaaS idempotency.
- Receipt identity is deterministic per successful settlement.
- Replays cannot create duplicate authoritative sale mutations.
