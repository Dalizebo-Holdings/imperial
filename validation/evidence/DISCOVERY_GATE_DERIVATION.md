# Phase 7 — Durable Evidence to Discovery Gate Derivation

## Purpose

This slice bridges the durable Phase 7 evidence ledger to the canonical
`ProductMarketValidationRegistry.discovery_gate()` evaluator.

It does **not** change the Discovery thresholds.

## Rules

- only durable decision-eligible evidence is reconstructed
- `TEST_FIXTURE` evidence is excluded
- `DISCOVERY_INTERVIEW` payloads are validated with `DiscoveryInterview`
- `DESIGN_PARTNER_COMMITMENT` payloads are validated with
  `DesignPartnerCommitment`
- the existing `ProductMarketValidationRegistry` computes the gate
- a `GATE_PROOF` is emitted only when the canonical state is `PASS`
- proof emission is prohibited while the gate is `PENDING`
- the emitted proof binds the canonical `evidence_digest`, ledger head and
  source evidence references
- Discovery thresholds remain authoritative even when operational collection is
  deferred
- Phase 8 remains blocked until the full Phase 7 closure engine returns
  `PHASE7_COMPLETE`

## Commands

Inspect the real-evidence-derived Discovery Gate:

```bash
python scripts/phase7-evidence-derive.py discovery
```

Attempt to emit the proof only after the canonical gate passes:

```bash
python scripts/phase7-evidence-derive.py discovery --emit-proof
```

Then ingest a successfully emitted proof:

```bash
python scripts/phase7-evidence-collect.py validate-inbox
python scripts/phase7-evidence-collect.py ingest-inbox
python scripts/phase7-evidence-collect.py progress
```

A non-zero result while the gate is `PENDING` is expected and is not a bypass.
