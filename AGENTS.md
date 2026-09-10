# Dalizebo Imperial — Codex Operating Instructions

## Execution Mode
Work autonomously and results-first.
Do not stop to present plans for approval.
Inspect the repository and working tree before changing files.
For large work, split into independent implementation/test chunks.
Run relevant validators after every completed slice.
Do not run historical builder scripts merely to rewrite status files.

## Current Handoff
Branch: phase8-development

Phase 8 engineering is ACTIVE_NON_CANONICAL / DEVELOPMENT_ONLY.

Canonical Phase 7 is NOT complete:
- Discovery Gate is deferred, not waived
- Release Gate 3 is not claimed PASS
- regulatory payment-scope confirmation remains pending
- PHASE7_COMPLETE must not be fabricated
- production authorization remains blocked

Do not alter evidence, metrics, attestations, or gate states simply to make a threshold pass.

## Current Worktree
First inspect:

    git status --short
    git diff

There may be uncommitted Phase 8 outbox-hardening files from the previous session.

Expected current slice:
- kernel/migrations/sql/0004_phase8_outbox_delivery_hardening.sql
- baas/events/runtime.py
- scripts/validate-phase8-outbox-hardening.py

A real runtime bug was fixed:
DEAD_LETTER delivery records must be terminal and must not be replanned by publish_committed().

## Current Validation State
Known result:

    OUTBOX HARDENING FAILED: baas=1 phase8=0

Interpretation:
- scripts/validate-phase8-outbox-hardening.py PASSED
- scripts/validate-baas-p0-events.py FAILED because of stale IMPLEMENTATION_STATUS expectations

The legacy validator currently expects old granular status text including:
    - [ ] Webhooks

Current baas/IMPLEMENTATION_STATUS.md correctly has:
    - [x] Events
    - [x] Webhooks
    - [x] Background Jobs
    DALIZEBO BAAS P0: COMPLETE

Fix validator drift without weakening its runtime behavioral assertions.

Required checks:

    python scripts/validate-baas-p0-events.py
    python scripts/validate-phase8-outbox-hardening.py

Only commit when both pass.

Suggested commit:
    Add Phase 8 durable outbox hardening

Push to:
    origin phase8-development

## Next Phase 8 Slice
After the current slice passes and is committed, implement durable PostgreSQL outbox-worker execution:

1. Worker claiming with SELECT ... FOR UPDATE SKIP LOCKED
2. Lease owner + lease expiry
3. Atomic claim semantics
4. Exponential retry scheduling with bounded attempts
5. Durable publish acknowledgements
6. DEAD_LETTER terminal persistence
7. Crash/expired-lease recovery
8. Tenant/correlation preservation
9. Concurrency tests proving workers do not double-claim events
10. PostgreSQL integration validation

Kernel remains authoritative for outbox event state.
Do not create a second competing event authority.

## Engineering Rules
- fail closed on cross-tenant access
- preserve idempotency
- preserve append-only/audit semantics
- no secrets in code, logs, evidence, migrations, or fixtures
- forward migrations; do not mutate historical migration files
- no destructive production operations
- use exact executable validation, not documentation-only claims
- keep changes focused and commit working slices

## Reporting
After work, report only:

### ✓ Completed
- concise completed results

### → Next
- next executable slice
