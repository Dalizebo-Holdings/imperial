# Phase 7 — Pilot Onboarding Start Execution

Creates a real `PILOT_ONBOARDING` evidence record from an already-ingested
`ACTIVE` design-partner commitment.

Safeguards:
- only current ACTIVE commitments may start onboarding
- pilot-status transitions are replayed from the durable ledger
- merchant identity/products are inherited from the commitment
- one onboarding per merchant
- explicit real evidence reference required
- TEST_FIXTURE excluded
- no automatic activation, onboarding completion, Gate 3 PASS, or Phase 8 authorization
