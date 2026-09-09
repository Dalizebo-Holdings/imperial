# Phase 7 — Durable Release Gate 1/2 Derivation

## Scope

This slice reconstructs the canonical release-gate attestation registry from the
durable real-evidence ledger.

It supports:

- Gate 1 — Discovery to Alpha
- Gate 2 — Alpha to Pilot

Gate 3 is intentionally excluded because it additionally depends on real pilot
metric and capacity evidence.

## Provenance

Only:

`TECHNICAL_ATTESTATION + REAL_OPERATIONAL`

records participate.

`TEST_FIXTURE` evidence is excluded.

## Gate 1

Gate 1 uses:

- the canonical Discovery Gate
- CORE_WORKFLOW_DEFINED
- KERNEL_BOUNDARIES_DOCUMENTED
- THREAT_MODEL_COMPLETED
- PAYMENT_ARCHITECTURE_DEFINED
- NO_UNRESOLVED_CRITICAL_REGULATORY_BLOCKER

If Discovery remains `PENDING`, Gate 1 cannot pass.

## Gate 2

Gate 2 uses:

- END_TO_END_COMMERCE_FLOW
- END_TO_END_POS_FLOW
- TENANT_ISOLATION_TESTS
- PAYMENT_CONSISTENCY_TESTS
- INVENTORY_CONSISTENCY_TESTS
- MONITORING
- ROLLBACK_PROCEDURE
- BACKUP_RESTORE_TEST

The canonical runtime performs evidence-expiry checks.

## Commands

```bash
python scripts/phase7-release-gates.py gate1
python scripts/phase7-release-gates.py gate2
```

Proof emission is PASS-only:

```bash
python scripts/phase7-release-gates.py gate1 --emit-proof
python scripts/phase7-release-gates.py gate2 --emit-proof
```

After a real proof is emitted:

```bash
python scripts/phase7-evidence-collect.py validate-inbox
python scripts/phase7-evidence-collect.py ingest-inbox
```

No threshold is waived and no release gate is marked PASS from repository code
alone.
