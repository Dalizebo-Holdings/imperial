# Phase 7 — Discovery + Design Partner Evidence Contract

## Purpose

Phase 7 validates that Dalizebo Commerce + POS solves a material merchant
problem before expansion.

This slice implements the validation control plane for the canonical discovery
and design-partner gate. It records evidence; it does not fabricate interviews,
customers, transactions, or product-market fit.

## Canonical Targets

Discovery / design partners:

- 20–30 discovery interviews
- 5–10 design partner commitments
- minimum 3 active pilot merchants
- at least 80% of interviewed merchants confirm the core problem is material

Design partners must have:

- active retail operations
- real inventory
- real customers
- transaction volume
- willingness to test Commerce and/or POS
- ability to provide structured feedback

## Evidence Model

### Discovery Interview

Required:

- interview_id
- merchant_ref
- merchant_segment
- conducted_at
- products discussed
- core_problem_material
- willingness_to_test
- structured_feedback_available
- evidence_ref

`merchant_ref` is an opaque reference such as `merchant://...`; names, emails,
phone numbers, payment data, and credentials are not stored in this control
plane.

### Design Partner Commitment

Required:

- commitment_id
- merchant_ref
- committed products
- committed_at
- active retail confirmation
- real inventory confirmation
- real customers confirmation
- transaction volume confirmation
- willingness to test
- structured feedback ability
- pilot status
- evidence_ref

Pilot status:

- CANDIDATE
- ACTIVE
- PAUSED
- WITHDRAWN

Only commitments satisfying every canonical selection criterion may be
registered.

## Gate

`DISCOVERY_DESIGN_PARTNER_GATE`

PASS requires:

- interviews >= 20
- material-problem confirmation rate >= 80%
- design partner commitments >= 5
- active pilot merchants >= 3

A PASS does not mean Phase 7 or product-market fit is complete. It only permits
progression into controlled pilot onboarding and metric collection.

## Integrity

- evidence IDs are immutable
- same ID + same content is idempotent
- same ID + different content fails closed
- duplicate merchant commitments fail closed
- timestamps must be timezone-aware
- evidence references use `evidence://`
- merchant references use `merchant://`
- no secret-bearing or direct contact fields
- no negative or fabricated metric counters

## Launch Capacity

The Phase 7 control plane carries the canonical Public MVP controlled cap:

- 100 organizations
- 250 POS branches
- 10,000 monthly orders

Capacity expansion is not authorized by this slice.

## Next Slice

Pilot onboarding + validation metrics + release-gate evidence.
