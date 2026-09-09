# Phase 7 — Release Gate Readiness Dashboard

## Purpose

Provide one command that explains why Release Gate 1 or Gate 2 is still
`PENDING` and which real evidence must be collected next.

The dashboard does not create evidence, mutate the durable ledger, emit proofs,
or change gate thresholds.

## Commands

```bash
python scripts/phase7-release-readiness.py
python scripts/phase7-release-readiness.py --gate 1
python scripts/phase7-release-readiness.py --gate 2
```

## Output

For each gate the dashboard reports:

- canonical state
- canonical unmet checks
- canonical evidence digest
- required technical attestations
- requirements currently satisfied
- requirements still missing/failed/expired according to the canonical gate
- Discovery dependency for Gate 1
- whether proof emission is currently allowed
- the next safe evidence-collection action

## Rules

- `TEST_FIXTURE` never counts
- no evidence is generated
- no gate state is overridden
- Gate 1 remains dependent on canonical Discovery PASS
- proof readiness is true only for canonical `PASS`
- Phase 8 remains blocked until `PHASE7_COMPLETE`
