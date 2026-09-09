# Phase 7 — Append-only Evidence Void

Purpose: invalidate an erroneous durable `PILOT_ONBOARDING_EVENT` without
editing or deleting the evidence ledger.

The original envelope remains in the append-only chain. A later
`EVIDENCE_VOID` envelope binds to the original envelope id and payload digest.
Gate 3 reconstruction verifies the void and excludes only that target event
from canonical replay.

Safeguards:
- ledger chain must verify before a void can be created
- target must be an existing non-fixture `PILOT_ONBOARDING_EVENT`
- target event id, envelope id, evidence type, and content digest are bound
- void must occur after its target
- duplicate voids are rejected
- no ledger file rewrite or deletion
- no gate PASS or Phase 8 authorization
