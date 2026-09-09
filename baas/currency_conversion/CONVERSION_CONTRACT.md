# Dalizebo BaaS Currency Conversion Runtime Contract

## Purpose

Currency Conversion BaaS provides a deterministic multi-currency conversion and
settlement layer on top of Payment Abstraction and Subscription Billing.

P0 owns the conversion ledger, settlement invariants, conversion-fee caps,
escrow feedback ordering, failed-transaction recovery path, and apology-credit
path. It does not capture market FX rates or execute provider network calls.

## Authority Boundary

Kernel and existing BaaS surfaces own:

- payment intent state
- refund authority
- invoice line semantics
- credit grants
- event delivery planning
- background job scheduling

Currency Conversion BaaS owns:

- conversion ledger entries
- conversion state machine
- conversion-fee cap enforcement
- escrow feedback timing discipline
- failed-transaction recovery orchestration
- apology-credit path metadata

## Money

All amounts are integer minor units with a three-letter uppercase currency.

Conversion fee is a percentage of the **confirmed** converted amount only.

Conversion fee cap is expressed as a percentage of the confirmed amount and is
enforced as an upper bound on the converted fee.

## Conversion Ledger Entry

Each conversion contains:

- conversion_id
- tenant scope
- source_currency
- destination_currency
- source_amount_minor
- destination_amount_minor
- conversion_fee_minor
- conversion_fee_percentage
- conversion_fee_cap_percentage
- confirmed_amount_minor
- source_payment_id
- destination_payment_id
- source_refund_id
- destination_refund_id
- apology_credit_id
- state
- idempotency_key
- requested_at
- confirmed_at
- escrow_feedback_at
- resolved_at
- resolution
- provider_reference
- kernel_authorization_ref
- correlation_id

## Conversion State Machine

Allowed states:

- PENDING
- CONFIRMED
- VOIDED
- RECOVERY_SCHEDULED
- RESOLVED

Transitions:

- PENDING -> CONFIRMED
- PENDING -> VOIDED
- PENDING -> RECOVERY_SCHEDULED
- CONFIRMED -> RESOLVED
- VOIDED -> RESOLVED
- RECOVERY_SCHEDULED -> RESOLVED

No other transitions are accepted.

## Settlement Invariants

For every CONFIRMED conversion:

1. source_amount_minor == destination_amount_minor + conversion_fee_minor
2. conversion_fee_minor >= 0
3. conversion_fee_minor <= confirmed_amount_minor * conversion_fee_cap_percentage / 100
4. conversion_fee_minor is computed from confirmed_amount_minor only

## Callback Discipline

The conversion state machine accepts only two settlement callbacks:

- confirmation
- void

Any other callback type leaves settlement state unchanged.

## Escrow Feedback Timing

For every RESOLVED conversion:

- escrow_feedback_at must be present
- resolved_at must be present
- escrow_feedback_at < resolved_at

## Failed Transaction Recovery

If the provider result outcome is FAILED or CANCELLED while the conversion is
PENDING, the conversion must:

1. not transition to CONFIRMED
2. void escrow reservation
3. schedule recovery via RECOVERY_SCHEDULED
4. emit a refund path for the source payment if it was captured
5. emit an apology-credit path if the destination was provisionally reserved

Recovery does not confirm the conversion.

## Apology Credit Path

When a conversion fails after destination provisioning, the BaaS creates apology
credit metadata that is structurally compatible with Subscription Billing credit
grants.

Apology credits:

- are tenant-scoped
- are integer minor-unit amounts
- have a reason describing the failure recovery reason
- may be applied to future invoices only

## Idempotency

Conversion planning is idempotent over:

- tenant organization_id
- conversion idempotency_key

The same key and same canonical request returns the same conversion id and plan.

## Events

Conversion events emit metadata suitable for Events BaaS/outbox:

- conversion.requested
- conversion.confirmed
- conversion.voided
- conversion.recovery_scheduled
- conversion.resolved

## Security

- `service=currency_conversion` is required.
- Kernel authorization evidence is mandatory.
- Cross-tenant conversion access fails closed.
- Provider credentials remain opaque references.
- No settlement callbacks other than confirmation and void mutate conversion state.
- No fee is charged on unconfirmed amounts.
- Conversion fee reputation activation is gated until the conversion is RESOLVED.
