# BaaS Payment Abstraction Runtime Contract

## Purpose

Payment Abstraction BaaS orchestrates licensed external payment providers while
preserving Kernel ownership of payment/refund state.

P0 creates provider-neutral operation plans, validates provider results against
Kernel payment lifecycle rules, produces explicit Kernel mutation sequences,
plans refunds, and performs reconciliation checks.

P0 does not execute provider network calls and does not persist a competing
authoritative payment state.

## Authority Boundary

Kernel owns:

- Payment Intent
- Status
- Amount
- Currency
- Provider
- Provider Reference
- Reconciliation State
- Refund State
- Idempotency
- Audit

BaaS Payments owns orchestration metadata only.

## Provider Registry

Each provider configuration contains:

- provider_id
- adapter_ref
- credential_ref
- supported_currencies
- capabilities
- enabled

Rules:

- provider-specific SDK/API logic remains behind `adapter_ref`
- credentials use only `secret://`, `vault://`, or `kms://`
- raw credentials/tokens are never stored or returned
- unsupported currencies/capabilities fail closed

P0 capabilities:

- AUTHORIZE
- CAPTURE
- REFUND

## Payment Request

A provider-neutral payment request contains:

- payment_request_id
- source_type (`ORDER` or `INVOICE`)
- source_ref
- amount_minor
- currency
- capture_mode (`AUTHORIZE_ONLY` or `AUTHORIZE_CAPTURE`)
- idempotency_key
- requested_at

Money follows Kernel rules:

- integer minor units
- three-letter uppercase currency
- amount > 0

## Idempotent Planning

Idempotency scope:

- organization_id
- environment_id
- provider_id
- idempotency_key

Same key + same canonical request returns the same payment ID/plan.

Same key + different canonical request fails closed.

## Provider Operation Plan

A payment request produces:

- payment_id
- provider_id
- provider_adapter_ref
- provider_credential_ref
- source_type
- source_ref
- amount_minor
- currency
- capture_mode
- idempotency_key
- tenant context
- correlation_id
- kernel_authorization_ref
- desired_kernel_status=`PENDING`
- audit_event
- payment_event

State:

`READY_FOR_PROVIDER_ADAPTER`

The P0 runtime does not call the provider.

## Provider Result

Safe provider results contain:

- payment_id
- provider_id
- provider_reference
- outcome
- amount_minor
- currency
- occurred_at
- error_code

Allowed outcomes:

- AUTHORIZED
- CAPTURED
- FAILED
- CANCELLED

Raw provider payloads, tokens, card data, cookies, headers, and credentials are
not accepted into the result record.

## Explicit Kernel Transition Planning

Kernel lifecycle:

`PENDING → AUTHORIZED → CAPTURED`

Failure/cancellation may occur before capture.

A provider result never causes hidden state mutation.

For immediate provider capture while Kernel is PENDING, BaaS produces the
explicit sequence:

`PENDING → AUTHORIZED → CAPTURED`

Every edge must be accepted by the injected Kernel transition validator.

## Refund Planning

Refunds require:

- current Kernel payment status = CAPTURED
- positive integer minor amount
- matching currency
- total refunded amount <= captured amount
- provider REFUND capability
- idempotency key
- explicit reason

The injected Kernel refund validator remains authoritative.

Output:

`READY_FOR_PROVIDER_REFUND_ADAPTER`

P0 does not execute the refund.

## Reconciliation

Reconciliation compares Kernel evidence with provider evidence:

- payment_id
- amount
- currency
- status
- provider reference

Result:

- MATCH
- MISMATCH

Mismatch details are stable metadata only and never include secrets or raw
provider bodies.

## Billing Boundary

Subscription Billing may create payment-retry intent metadata.

Payment Abstraction may translate a validated retry request into a provider
operation plan, but Billing does not select provider SDKs or perform charging.

## Current Kernel Source-Link Limitation

The current Kernel commerce `PaymentState` is order-linked.

P0 Payments supports source metadata for `ORDER` and `INVOICE`, but invoice-backed
authoritative payment persistence must use a future Kernel payment-source
extension before production activation.

P0 does not bypass this limitation by creating a competing authoritative state.

## Security

- `service=payments` is required.
- Kernel authorization evidence is mandatory.
- Cross-tenant payment/refund access fails closed.
- Provider credentials remain opaque references.
- Raw payment credentials/card authentication data are forbidden.
- Payment/refund operations are idempotent.
- No hidden payment transitions are allowed.
