# Phase 7 — PMF Decision and Closure Gate

## Purpose

The Phase 7 closure gate decides whether Product-Market Validation has enough
real evidence to advance to Phase 8 — Platform Hardening.

Installing this evaluator does not itself complete Phase 7.

## Required Gate Proofs

Phase 7 closure requires decision-eligible evidence for:

1. Discovery + Design Partner Gate — PASS
2. Pilot Exit Gate — PASS
3. Release Gate 1 — PASS
4. Release Gate 2 — PASS
5. Release Gate 3 — PASS
6. Operational Readiness — EVIDENCE_AVAILABLE
7. Public MVP First-90-Day Gate — PASS

Every proof must be bound to an append-only Evidence Ledger envelope.

## Public MVP First-90-Day Gate

Canonical targets from `validation/PUBLIC_MVP_CRITERIA.md`:

- 50 activated organizations
- 30 monthly transacting organizations
- 20 active for 3 consecutive months
- monthly logo churn < 5%
- 30% reach first transaction within 24 hours
- 60% weekly active usage
- payment reconciliation >= 99.5%
- uptime >= 99.5%
- P95 core API latency < 500 ms
- checkout API P95 < 1.5 s excluding payment provider
- at least 10 paying customers
- at least 3 customer references
- no critical tenant isolation defect
- successful backup restore test

The control plane uses explicit denominators for churn, first-24-hour activation,
weekly usage, reconciliation, and uptime so rates are deterministic.

The evidence window must span at least 90 days.

## Decision States

- CONTINUE_VALIDATION
- PHASE7_COMPLETE

`PHASE7_COMPLETE` requires every gate above to pass with non-fixture evidence.

A missing, expired, fixture-only, unmatched, or failed proof results in
`CONTINUE_VALIDATION`.

## Next Phase

Only `PHASE7_COMPLETE` authorizes progression to:

Phase 8 — Platform Hardening.
