# Phase 7 — Durable Release Gate 3 Derivation

## Purpose

Reconstruct canonical Release Gate 3 from the durable real-evidence ledger.

This implementation reuses `PilotValidationRegistry` rather than duplicating
Gate 3 logic.

## Durable evidence replayed

- `DESIGN_PARTNER_COMMITMENT`
- `PILOT_STATUS_TRANSITION`
- `PILOT_ONBOARDING`
- `PILOT_ONBOARDING_EVENT`
- `PILOT_METRIC_SNAPSHOT`
- `CAPACITY_SNAPSHOT`
- `TECHNICAL_ATTESTATION`

`TEST_FIXTURE` is excluded.

## Canonical Gate 3 requirements

The existing runtime evaluates:

- real transactions
- payment reconciliation >= 99.5%
- at least 5 completed onboardings
- at least 80% first sale within 24 hours
- at least 2 merchants willing to pay
- zero critical cross-tenant defects in the metric snapshot
- controlled capacity within launch caps
- `SUPPORT_PROCESS`
- `RECOVERY_PROCEDURES`
- `NO_MATERIAL_TENANT_ISOLATION_DEFECT`

Attestation expiry remains enforced by the canonical runtime.

## Usage

List available durable sources:

```bash
python scripts/phase7-release-gate3.py sources
```

Derive:

```bash
python scripts/phase7-release-gate3.py derive   --snapshot-id <real metric snapshot id>   --capacity-snapshot-id <real capacity snapshot id>
```

Emit a proof only after canonical PASS:

```bash
python scripts/phase7-release-gate3.py derive   --snapshot-id <real metric snapshot id>   --capacity-snapshot-id <real capacity snapshot id>   --emit-proof
```

Then use the normal inbox validation/ingestion workflow.

No Gate 3 PASS is inferred from code, test fixtures, or missing evidence.
Phase 8 remains blocked until the PMF decision gate emits `PHASE7_COMPLETE`.
