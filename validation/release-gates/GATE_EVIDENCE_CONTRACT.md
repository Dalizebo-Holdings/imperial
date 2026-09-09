# Phase 7 — Release-Gate Evidence Contract

## Purpose

Release gates are evidence-based decisions.

A repository file or status statement alone does not prove a production,
merchant, regulatory, reliability, or commercial outcome.

## Gate 1 — Discovery to Alpha

Requires:

- problem validation
- design partners
- core workflow defined
- Kernel boundaries documented
- threat model completed
- payment architecture defined
- no unresolved critical regulatory blocker

Problem validation/design partners come from the Discovery + Design Partner
gate. The remaining requirements require explicit evidence attestations.

## Gate 2 — Alpha to Pilot

Requires explicit evidence for:

- end-to-end Commerce flow
- end-to-end POS flow
- tenant isolation tests
- payment consistency tests
- inventory consistency tests
- monitoring
- rollback procedure
- backup restore test

## Gate 3 — Pilot to Public MVP

Requires:

- real transactions
- stable reconciliation
- repeatable onboarding
- support process
- recovery procedures
- at least 2 merchants willing to pay
- no material tenant isolation defect
- controlled capacity remains within cap

Real-transaction, reconciliation, onboarding, willingness-to-pay, and
cross-tenant metrics are derived from recorded pilot evidence.

Support/recovery/isolation attestations still require evidence references.

## Evidence Attestation

Each technical/operational attestation records:

- attestation_id
- requirement
- satisfied
- observed_at
- evidence_ref
- optional valid_until
- safe metadata

Expired evidence does not satisfy a gate.

Same attestation ID with changed content fails closed.

## Result

Gate states:

- PASS
- PENDING

No code path auto-promotes Phase 7 to Product-Market Fit.
