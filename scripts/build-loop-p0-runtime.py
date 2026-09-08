#!/usr/bin/env python3

from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
LOOP = ROOT / "orchestration/loop-os"
RUNTIME = LOOP / "runtime"

required = [
    LOOP / "README.md",
    LOOP / "EXECUTION_MODEL.md",
    LOOP / "RUNTIME_SCHEMA.md",
    LOOP / "STATE_MACHINE.md",
    RUNTIME / "job_model.py",
    RUNTIME / "state_machine.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(f"ERROR: missing Loop OS artifact: {path}")

for path in [
    RUNTIME / "job_model.py",
    RUNTIME / "state_machine.py",
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
- [ ] Queue adapter
- [ ] Worker execution contract
- [ ] Loop audit adapter

## Current Next Work

Implement Loop OS P0 queue adapter + worker execution contract.
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

Loop OS P0 runtime schema and state machine complete.

## Algorithm OS

P0 status: COMPLETE

## Loop OS

Runtime job schema: COMPLETE

Deterministic state machine: COMPLETE

Bounded retry rules: COMPLETE

Timeout evaluation: COMPLETE

Dead-letter transition: COMPLETE

Idempotency fingerprint: COMPLETE

Queue adapter: PENDING

Worker execution contract: PENDING

Loop audit adapter: PENDING

## Integrations OS

Connector standard: DEFINED

Connector registry and runtime contracts: PENDING

## Next Work

Loop OS P0 — queue adapter + worker execution contract.

## Governing Rule

Loop OS execution remains bounded, observable, idempotent, timeout-controlled,
and subject to upstream Algorithm OS, Pillars OS, and Kernel authorization
boundaries.
""",
encoding="utf-8",
)

print("OK: Loop OS runtime schema installed.")
print("OK: Loop OS deterministic state machine installed.")
print("NEXT: Loop OS queue adapter + worker execution contract.")
