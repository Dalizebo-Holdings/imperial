# Phase 7 — Merchant Feedback Evidence Contract

## Canonical Categories

- ONBOARDING
- COMMERCE
- POS
- INVENTORY
- PAYMENTS
- REPORTING
- PERFORMANCE
- RELIABILITY
- SUPPORT
- PRICING

## Required Classification

Each feedback item records:

- merchant reference
- problem
- frequency
- severity
- business impact
- requested outcome
- existing workaround
- product decision
- evidence reference

Merchant references remain opaque (`merchant://...`).

## Product Decision

P0 control-plane states:

- PENDING
- INVESTIGATE
- PLANNED
- DECLINED
- DELIVERED

A decision change is explicit and evidence-backed.

## Integrity

- same feedback ID + same content is idempotent
- same feedback ID + changed content fails closed
- frequency is a positive integer
- severity is P0/P1/P2/P3
- text is bounded and rejects obvious credential/payment-card material
- evidence references use `evidence://`
