# Phase 7 — Pilot Onboarding Evidence Contract

## Purpose

This contract records real merchant onboarding evidence for controlled Commerce
and POS pilots.

It does not create merchants, transactions, or successful onboarding outcomes
from code alone.

## Canonical Flow

Organization Creation
→ Store Setup
→ Branch Setup
→ Staff
→ Product Import
→ Inventory Setup
→ Payment Setup
→ Test Sale
→ First Live Transaction

For Commerce-only pilots, Branch Setup and Staff are not required.

For POS pilots, the full branch/staff path is required.

## Eligibility

A pilot onboarding may start only from a canonical design-partner commitment
whose:

- merchant reference matches
- pilot status is ACTIVE
- products include the onboarding products
- canonical partner-selection evidence remains satisfied

## Event Ledger

Each onboarding event records:

- event_id
- onboarding_id
- merchant_ref
- step
- status: SUCCESS or FAILED
- occurred_at
- evidence_ref
- optional failure_code
- training_required
- support_intervention
- safe metadata

Evidence is append-only/idempotent:

- same event ID + same material → replay-safe
- same event ID + different material → fail closed

Successful steps must follow the canonical product-specific sequence.

Failed attempts may be followed by a later successful retry.

## Target

First successful live transaction within 24 hours of onboarding start.

Derived onboarding evidence includes:

- setup duration
- import failure count
- payment-setup failure count
- training requirement count
- support intervention count
- time to first transaction
- within-24-hours result

## Privacy

The control plane uses opaque:

- `merchant://...`
- `evidence://...`

It rejects direct-contact, credential, payment-card, bank-account, token, and
secret-bearing metadata.

## State

`PILOT_ONBOARDING_EVIDENCE_READY`
