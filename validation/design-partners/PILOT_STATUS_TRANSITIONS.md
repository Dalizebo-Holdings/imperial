# Phase 7 — Durable Pilot Status Transition Evidence

Design-partner commitments begin as `CANDIDATE`. Canonical pilot onboarding
requires an `ACTIVE` design partner. This slice adds append-only
`PILOT_STATUS_TRANSITION` evidence and replays those transitions during durable
Discovery Gate derivation.

Canonical transitions:
- `CANDIDATE -> ACTIVE/WITHDRAWN`
- `ACTIVE -> PAUSED/WITHDRAWN`
- `PAUSED -> ACTIVE/WITHDRAWN`
- `WITHDRAWN` is terminal

Usage:

```bash
python scripts/phase7-pilot-status.py list
python scripts/phase7-pilot-status.py transition \
  --commitment-id <real commitment id> \
  --target-status ACTIVE \
  --evidence-ref evidence://real-pilot-start-agreement
python scripts/phase7-evidence-collect.py validate-inbox
python scripts/phase7-evidence-collect.py ingest-inbox
python scripts/phase7-evidence-derive.py discovery
```

`from_status` and merchant identity are derived from durable evidence. No
transition is automatic, thresholds are not waived, and Phase 8 remains blocked
until `PHASE7_COMPLETE`.
