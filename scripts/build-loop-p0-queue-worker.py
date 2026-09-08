#!/usr/bin/env python3

from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
LOOP = ROOT / "orchestration/loop-os"
RUNTIME = LOOP / "runtime"

required = [
    LOOP / "QUEUE_ADAPTER.md",
    LOOP / "WORKER_CONTRACT.md",
    RUNTIME / "job_model.py",
    RUNTIME / "state_machine.py",
    RUNTIME / "queue_adapter.py",
    RUNTIME / "worker_contract.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(f"ERROR: missing Loop OS artifact: {path}")

for path in [
    RUNTIME / "job_model.py",
    RUNTIME / "state_machine.py",
    RUNTIME / "queue_adapter.py",
    RUNTIME / "worker_contract.py",
]:
    py_compile.compile(str(path), doraise=True)

(LOOP / "IMPLEMENTATION_STATUS.md").write_text(
"""# Loop OS Implementation Status

## Phase

Phase 3

## P0 Components

- [x] Runtime job schema
- [x] Deterministic state machine
- [x] Bounded retry rules
- [x] Timeout evaluation
- [x] Dead-letter transition
- [x] Idempotency fingerprint
- [x] Queue adapter
- [x] Worker execution contract
- [ ] Loop audit adapter

## Current Next Work

Implement Loop OS P0 Audit Adapter, then close Loop OS P0.
""",
encoding="utf-8",
)

(ROOT / "orchestration/STATUS.md").write_text(
"""# Phase 3 Orchestration Status

## Phase

Phase 3 — Algorithm OS + Loop OS + Integrations OS

## Prerequisite

Phase 2 canonical catalogue: 269 / 269 classified

## Current Stage

Loop OS P0 queue and worker contract complete.

## Algorithm OS

P0 status: COMPLETE

## Loop OS

Runtime job schema: COMPLETE

Deterministic state machine: COMPLETE

Bounded retry rules: COMPLETE

Timeout evaluation: COMPLETE

Dead-letter transition: COMPLETE

Idempotency fingerprint: COMPLETE

Queue adapter: COMPLETE

Worker execution contract: COMPLETE

Loop audit adapter: PENDING

## Integrations OS

Connector standard: DEFINED

Connector registry and runtime contracts: PENDING

## Next Work

Loop OS P0 — Audit Adapter.

## Governing Rule

Loop OS workers may invoke handlers only after explicit Pillars OS approval and
Dalizebo Kernel authorization. Retries remain bounded and duplicate execution
must remain safe.
""",
encoding="utf-8",
)

print("OK: Loop OS Queue Adapter installed.")
print("OK: Loop OS Worker Execution Contract installed.")
print("NEXT: Loop OS P0 Audit Adapter.")
