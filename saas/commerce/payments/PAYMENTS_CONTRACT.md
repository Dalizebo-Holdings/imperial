# Commerce P0 — Payments Contract

## Purpose

Dalizebo Commerce Payments is the SaaS orchestration layer over BaaS Payment
Abstraction and Kernel Payment authority.

Commerce never talks directly to a payment provider and never owns a competing
Payment state machine.

## Payment Start

P0 payment start requires:

- authoritative Order evidence
- Order status = PLACED
- amount_minor > 0
- three-letter currency
- provider_id
- capture mode
- idempotency key

Commerce delegates provider planning to BaaS Payment Abstraction.

It then creates a shared `PAYMENT` platform command with:

- order_id
- status = PENDING
- amount_minor
- currency
- provider_id

Provider credentials remain inside the BaaS adapter boundary and are never
copied into Commerce command metadata.

## Provider Result

Provider results are first validated by BaaS Payment Abstraction.

BaaS produces an explicit Kernel transition sequence such as:

`PENDING → AUTHORIZED → CAPTURED`

Commerce converts every edge into an explicit shared Payment transition command.

There are no hidden payment transitions.

## Order Confirmation

When the final validated payment transition is `CAPTURED`, Commerce explicitly
plans:

`Order PLACED → CONFIRMED`

using Kernel `OrderState`.

Failed/cancelled payment does not confirm the Order.

## Idempotency

- provider payment planning uses BaaS idempotency
- shared Payment creation uses the same stable payment identity
- payment transition command IDs derive from Payment/result/edge identity
- retries do not create duplicate authoritative payments

## Security

- exact-tenant Order and Payment evidence required
- Kernel authorization evidence required
- raw card/authentication/provider credential data forbidden
- provider network execution remains behind licensed BaaS adapters
