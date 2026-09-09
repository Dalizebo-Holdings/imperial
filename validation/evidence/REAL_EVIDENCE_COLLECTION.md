# Phase 7 — Real Evidence Collection Kit

## Purpose

This kit turns the durable Phase 7 evidence ledger into an operator-facing
collection workflow.

It does not fabricate evidence and it does not mark Phase 7 complete.

## Default Paths

Ledger:

`~/.local/share/dalizebo/imperial/validation/evidence-ledger.jsonl`

Evidence inbox:

`~/.local/share/dalizebo/imperial/validation/inbox/`

Both paths can be overridden.

## Workflow

Initialize the durable ledger:

```bash
python scripts/validation-evidence.py init
```

Create a private evidence inbox with templates:

```bash
python scripts/phase7-evidence-collect.py init-inbox
```

Edit only the copied inbox files outside Git.

Validate all evidence before writing:

```bash
python scripts/phase7-evidence-collect.py validate-inbox
```

Ingest replay-safely:

```bash
python scripts/phase7-evidence-collect.py ingest-inbox
```

Review progress:

```bash
python scripts/phase7-evidence-collect.py progress
```

Run the PMF closure evaluator only when the required gate proofs exist:

```bash
python scripts/evaluate-phase7-pmf.py proofs.json
```

## Template Types

- discovery-interview
- design-partner-commitment
- pilot-onboarding
- pilot-metric-snapshot
- capacity-snapshot
- technical-attestation
- merchant-feedback
- support-evidence
- incident-evidence
- public-mvp-90d
- gate-proof

The templates contain `__REPLACE__` sentinels. The collection CLI rejects any
file that still contains a placeholder.

## Provenance

Template origin defaults are conservative:

- merchant interviews/commitments/feedback/onboarding → REAL_MERCHANT
- operational support/incidents/attestations/capacity → REAL_OPERATIONAL
- pilot/product metrics → REAL_RELIABILITY
- public-MVP commercial aggregate → REAL_COMMERCIAL
- gate proof → operator must set the appropriate real origin

The origin is a declared provenance class. It does not independently prove the
external event happened.

## Batch Safety

Before any batch is appended, the CLI:

1. parses every JSON file
2. rejects placeholders
3. verifies required fields
4. computes canonical payload SHA-256
5. validates every EvidenceEnvelope
6. replays all entries against a reconstructed in-memory ledger
7. fails the entire preflight on any conflict

After preflight, records are appended using the durable store's lock/fsync path.

A process crash during append can leave a partial batch, but rerunning the same
batch is replay-safe because envelope IDs and evidence references are
idempotent.

## Progress

`progress` reports:

- total ledger records
- decision-eligible records
- fixture records
- counts by evidence type
- discovery interview count
- design-partner commitment count
- ACTIVE partner evidence count
- pilot onboarding evidence count
- metric snapshot count
- operational evidence count
- required PMF proof labels present/missing

Progress is evidence presence only. It does not substitute for the existing
Discovery, Pilot Exit, Release Gate, Operational Readiness, or Public MVP
evaluators.

## Phase Rule

Phase 8 remains blocked until the PMF decision engine returns:

`PHASE7_COMPLETE`
