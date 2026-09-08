# BaaS Subscription Billing Runtime Contract

## Purpose

Subscription Billing BaaS converts versioned plan pricing plus reconciled Usage
Metering aggregates into tenant-scoped invoices, credits, entitlements, billing
events, and payment-retry intents.

P0 does not execute charges. Payment execution belongs to Payments BaaS.

## Canonical Model

Billing:

Subscription
+
Metered Usage

Pipeline:

Platform Usage
→ Metering Event
→ Aggregation
→ Rating
→ Billing
→ Invoice
→ Payment Abstraction
→ Reconciliation

## Money

Billing follows Kernel commerce money rules:

- integer minor units
- three-letter uppercase currency
- floating point money is prohibited
- invoice totals may not be negative

Metered quantities are Decimal strings from Usage Metering.

Usage line rating uses:

`billable_quantity × unit_price_minor`

with explicit `ROUND_HALF_UP` conversion to integer minor units.

## Plan Version

Every immutable plan version contains:

- plan_id
- version
- name
- currency
- billing_interval
- recurring_amount_minor
- metered_rates
- entitlements
- effective_at
- state

Metered rates contain:

- metric
- unit
- unit_price_minor
- included_quantity

Invoices always retain the exact plan version used for rating.

## Subscription

Each subscription contains:

- subscription_id
- tenant scope
- customer_ref
- plan_id
- plan_version
- status
- current_period_start
- current_period_end
- cancel_at_period_end
- created_at
- updated_at

P0 states:

- ACTIVE
- PAST_DUE
- CANCELLED

Illegal transitions fail closed.

## Usage Evidence

Billing consumes aggregate evidence from Usage Metering:

- aggregate_id
- tenant scope
- metric
- unit
- total_quantity
- event_count
- period_start
- period_end
- source_hash

Rules:

- tenant must match the subscription
- aggregate period must match the subscription billing period
- metric/unit must match a versioned plan rate
- duplicate aggregate IDs are rejected
- source hashes are retained for reconciliation

Billing never edits raw usage or Usage Metering aggregates.

## Credits

Credits are tenant-scoped integer minor-unit grants.

A credit may only be applied to an invoice in the same currency and tenant.

Credit application cannot make an invoice negative.

Remaining credit is tracked separately from the immutable grant descriptor.

## Invoice

Invoice states:

- DRAFT
- OPEN
- VOID

P0 invoice lines:

- RECURRING
- METERED
- CREDIT

Every invoice retains:

- invoice_id
- subscription_id
- tenant scope
- plan_id
- plan_version
- currency
- period_start
- period_end
- lines
- subtotal_minor
- credit_minor
- total_minor
- usage_source_hash
- calculation_hash
- state
- created_at
- opened_at

`calculation_hash` covers the deterministic invoice calculation manifest.

## Idempotent Invoice Generation

Invoice identity is deterministic over:

- subscription
- billing period
- plan version
- ordered usage aggregate IDs/source hashes
- selected credit IDs

The same exact input returns the same invoice.

Conflicting reuse of the same invoice identity is impossible because the
calculation manifest is hashed into the identity.

## Entitlements

Entitlements resolve from the subscription's exact plan version.

Billing returns entitlement metadata only. Product enforcement remains with the
service consuming those entitlements.

## Billing Events

P0 emits metadata events for:

- subscription.created
- subscription.status_changed
- invoice.drafted
- invoice.opened
- credit.issued
- payment_retry.requested

These are suitable for the existing Events BaaS/outbox path.

## Payment Retry Boundary

Billing may create a `PaymentRetryIntent` for an OPEN invoice.

The intent contains:

- retry_id
- invoice_id
- attempt
- amount_minor
- currency
- idempotency_key
- kernel_authorization_ref
- audit_event
- billing_event

State:

`READY_FOR_PAYMENT_ABSTRACTION`

No provider charge, token handling, or payment state transition occurs inside
Billing BaaS.

## Reconciliation

Invoice reconciliation recomputes:

- recurring line amount
- each metered line amount from Usage Metering evidence and exact plan version
- credit line totals
- invoice total
- usage source hash
- calculation hash

Any mismatch fails reconciliation.

## Security

- `service=subscription_billing` is required.
- Kernel authorization evidence is mandatory.
- Cross-tenant subscription/invoice/credit access fails closed.
- Money uses integer minor units only.
- Pricing is versioned.
- Payment provider logic is forbidden in Billing BaaS.
- No hidden payment transitions are allowed.
