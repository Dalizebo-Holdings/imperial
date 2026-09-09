# Phase 7 — Real Evidence Operations

## Purpose

The PMF decision engine is already installed. This operational layer makes its
evidence ledger durable and executable for real Phase 7 collection.

It does **not** create evidence or mark Phase 7 complete.

## Storage

Default ledger:

`~/.local/share/dalizebo/imperial/validation/evidence-ledger.jsonl`

Override with:

`DALIZEBO_VALIDATION_LEDGER=/secure/path/evidence-ledger.jsonl`

The ledger is intentionally outside the Git repository.

Permissions are set to owner read/write (`0600`).

## Evidence Envelope Input

Create a JSON file containing:

```json
{
  "envelope_id": "unique-stable-id",
  "evidence_type": "DISCOVERY_GATE_PROOF",
  "origin": "REAL_MERCHANT",
  "observed_at": "2026-09-09T10:00:00+02:00",
  "evidence_ref": "evidence://phase7/discovery/gate-proof-001",
  "source_system_ref": "source://validation/discovery-registry",
  "payload": {
    "evidence_digest": "<64-char digest from the evaluated gate>"
  }
}
```

Do not manually add `content_sha256` when using the CLI; it computes the
canonical digest before ingestion.

Allowed origins:

- REAL_MERCHANT
- REAL_OPERATIONAL
- REAL_COMMERCIAL
- REAL_RELIABILITY
- TEST_FIXTURE

`TEST_FIXTURE` never counts toward closure.

## Commands

Initialize:

```bash
python scripts/validation-evidence.py init
```

Ingest:

```bash
python scripts/validation-evidence.py ingest evidence.json
```

Verify:

```bash
python scripts/validation-evidence.py verify
```

Status:

```bash
python scripts/validation-evidence.py status
```

Export a verified copy:

```bash
python scripts/validation-evidence.py export /secure/backup/evidence-ledger.jsonl
```

## PMF Evaluation

Prepare a proof manifest containing the seven required proofs:

```json
{
  "proofs": [
    {
      "label": "discovery",
      "state": "PASS",
      "evidence_digest": "<digest>",
      "evidence_ref": "evidence://..."
    },
    {
      "label": "pilot_exit",
      "state": "PASS",
      "evidence_digest": "<digest>",
      "evidence_ref": "evidence://..."
    },
    {
      "label": "release_gate_1",
      "state": "PASS",
      "evidence_digest": "<digest>",
      "evidence_ref": "evidence://..."
    },
    {
      "label": "release_gate_2",
      "state": "PASS",
      "evidence_digest": "<digest>",
      "evidence_ref": "evidence://..."
    },
    {
      "label": "release_gate_3",
      "state": "PASS",
      "evidence_digest": "<digest>",
      "evidence_ref": "evidence://..."
    },
    {
      "label": "operational_readiness",
      "state": "EVIDENCE_AVAILABLE",
      "evidence_digest": "<digest>",
      "evidence_ref": "evidence://..."
    },
    {
      "label": "public_mvp_90d",
      "state": "PASS",
      "evidence_digest": "<digest>",
      "evidence_ref": "evidence://..."
    }
  ]
}
```

Evaluate:

```bash
python scripts/evaluate-phase7-pmf.py proofs.json
```

The evaluator prints either:

- `CONTINUE_VALIDATION`
- `PHASE7_COMPLETE`

Only the latter authorizes Phase 8.

## Public MVP Snapshot

To calculate the canonical first-90-day gate from real aggregate counters:

```bash
python scripts/evaluate-phase7-pmf.py   --public-mvp-snapshot public-mvp-90d.json
```

This calculates and prints the gate state/digest but does not automatically
ingest it as real evidence. Review the source aggregates, then ingest a bound
evidence envelope explicitly.

## Integrity

- The durable store reconstructs and verifies the runtime chain on every load.
- Appends use an exclusive filesystem lock.
- Writes are flushed and `fsync()` is called.
- Duplicate IDs with changed evidence fail closed.
- Evidence remains outside Git by default.
- The system validates declared provenance and content integrity; it does not
  independently prove external events occurred.
