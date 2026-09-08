#!/usr/bin/env python3

from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
LOOP = ROOT / "orchestration/loop-os"
RUNTIME = LOOP / "runtime"

required = [
    LOOP / "AUDIT_ADAPTER.md",
    RUNTIME / "job_model.py",
    RUNTIME / "state_machine.py",
    RUNTIME / "queue_adapter.py",
    RUNTIME / "worker_contract.py",
    RUNTIME / "audit_adapter.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(f"ERROR: missing Loop OS artifact: {path}")

for path in [
    RUNTIME / "job_model.py",
    RUNTIME / "state_machine.py",
    RUNTIME / "queue_adapter.py",
    RUNTIME / "worker_contract.py",
    RUNTIME / "audit_adapter.py",
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
- [x] Loop audit adapter

## P0 Status

COMPLETE

## Current Next Work

Proceed to Integrations OS P0 connector registry + runtime contracts.
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

Loop OS P0 complete.

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

Loop audit adapter: COMPLETE

P0 status: COMPLETE

## Integrations OS

Connector standard: DEFINED

Connector registry: PENDING

Runtime contracts: PENDING

## Next Work

Integrations OS P0 — connector registry + runtime contracts.

## Governing Rule

External effects remain governed by Algorithm OS planning, Pillars OS policy,
Dalizebo Kernel authorization, Loop OS bounded execution, and explicit
Integrations OS connector contracts.
""",
encoding="utf-8",
)

print("OK: Loop OS Audit Adapter installed.")
print("OK: Loop OS P0 marked COMPLETE.")
print("NEXT: Integrations OS P0 connector registry + runtime contracts.")
