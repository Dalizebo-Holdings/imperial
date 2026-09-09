# Commerce P0 — Refund Contract

## Purpose

Dalizebo Commerce Refunds closes the Commerce MVP refund path while preserving
Kernel and BaaS authority.

Commerce does not own a competing Refund database or provider integration.

## Preconditions

A provider refund requires:

- product = COMMERCE
- Store context
- exact-tenant Order evidence
- Order status CONFIRMED or COMPLETED
- exact-tenant Payment evidence
- Payment status CAPTURED
- amount_minor > 0
- three-letter currency
- captured amount and previous refund evidence
- provider_id and provider_reference
- idempotency key

## Shared Kernel Refund

Kernel `Refund` validates:

`previously_refunded_minor + amount_minor <= captured_amount_minor`

Currency must match the captured Payment.

## Provider Boundary

Commerce delegates provider refund planning to:

`BaaS Payment Abstraction.create_refund_plan()`

Provider credentials remain references inside BaaS and are never resolved in
Commerce.

Provider operation state:

`READY_FOR_PROVIDER_REFUND_ADAPTER`

## Completion

Commerce records a shared `REFUND` command only after explicit successful
provider-completion evidence matches the approved BaaS refund plan.

Partial cumulative refund:

- Payment remains CAPTURED

Full cumulative refund:

- explicit Payment CAPTURED → REFUNDED transition

## Audit

The shared ProductCommand plan supplies the authoritative audit metadata for
the REFUND mutation.

The Commerce settlement additionally exposes safe refund completion audit
metadata containing IDs, amount, currency, provider ID/reference, tenant scope,
and correlation ID.

No raw provider credentials, card data, tokens, or secret values are allowed.

## Idempotency

BaaS refund planning and shared REFUND mutation use stable idempotency keys.

Same idempotency scope + different refund material fails closed.

## State

Successful provider evidence produces:

`READY_FOR_KERNEL_REFUND_TRANSACTION_ADAPTER`
