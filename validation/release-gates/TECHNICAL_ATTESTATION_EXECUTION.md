# Phase 7 — Technical Attestation Execution

## Purpose

Record real `REAL_OPERATIONAL` evidence for Release Gate 1 and Gate 2 without
manually editing JSON.

A repository file or implementation status alone is not evidence of a
production, regulatory, reliability, or operational outcome.

## Gate 1 Attestations

- `CORE_WORKFLOW_DEFINED`
- `KERNEL_BOUNDARIES_DOCUMENTED`
- `THREAT_MODEL_COMPLETED`
- `PAYMENT_ARCHITECTURE_DEFINED`
- `NO_UNRESOLVED_CRITICAL_REGULATORY_BLOCKER`

Gate 1 also requires the canonical Discovery Gate to pass.

## Gate 2 Attestations

- `END_TO_END_COMMERCE_FLOW`
- `END_TO_END_POS_FLOW`
- `TENANT_ISOLATION_TESTS`
- `PAYMENT_CONSISTENCY_TESTS`
- `INVENTORY_CONSISTENCY_TESTS`
- `MONITORING`
- `ROLLBACK_PROCEDURE`
- `BACKUP_RESTORE_TEST`

## Usage

List requirements:

```bash
python scripts/phase7-technical-attestation.py requirements
python scripts/phase7-technical-attestation.py requirements --gate 1
python scripts/phase7-technical-attestation.py requirements --gate 2
```

Record an attestation only after you have genuine supporting evidence:

```bash
python scripts/phase7-technical-attestation.py record   TENANT_ISOLATION_TESTS   --satisfied yes   --evidence-ref evidence://your-real-evidence-reference
```

Optional expiry:

```bash
python scripts/phase7-technical-attestation.py record   BACKUP_RESTORE_TEST   --satisfied yes   --evidence-ref evidence://your-real-evidence-reference   --valid-until 2026-12-31T23:59:59+02:00
```

Then:

```bash
python scripts/phase7-evidence-collect.py validate-inbox
python scripts/phase7-evidence-collect.py ingest-inbox

python scripts/phase7-release-gates.py gate1
python scripts/phase7-release-gates.py gate2
```

## Safeguards

- `origin` is fixed to `REAL_OPERATIONAL`
- only canonical Gate 1/2 requirement names are accepted
- `TEST_FIXTURE` is never generated
- evidence references must be explicit and non-placeholder
- expiry timestamps must be timezone-aware ISO-8601
- `satisfied` must be explicitly supplied
- records are written owner-only (`0600`)
- Gate 1/2 PASS remains controlled by the canonical evaluator
- Phase 8 remains blocked until `PHASE7_COMPLETE`
