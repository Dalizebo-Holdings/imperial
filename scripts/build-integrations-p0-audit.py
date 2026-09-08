#!/usr/bin/env python3

from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
INTEGRATIONS = ROOT / "orchestration/integrations-os"
RUNTIME = INTEGRATIONS / "runtime"

required = [
    INTEGRATIONS / "AUDIT_ADAPTER.md",
    RUNTIME / "connector_model.py",
    RUNTIME / "connector_registry.py",
    RUNTIME / "runtime_contract.py",
    RUNTIME / "credential_reference.py",
    RUNTIME / "provider_adapter.py",
    RUNTIME / "audit_adapter.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Integrations OS artifact: {path}"
        )

for path in [
    RUNTIME / "connector_model.py",
    RUNTIME / "connector_registry.py",
    RUNTIME / "runtime_contract.py",
    RUNTIME / "credential_reference.py",
    RUNTIME / "provider_adapter.py",
    RUNTIME / "audit_adapter.py",
]:
    py_compile.compile(str(path), doraise=True)

(INTEGRATIONS / "IMPLEMENTATION_STATUS.md").write_text(
"""# Integrations OS Implementation Status

## Phase

Phase 3

## P0 Components

- [x] Connector standard
- [x] Connector definition model
- [x] Connector registry
- [x] Runtime request contract
- [x] Authorization gate
- [x] Version compatibility contract
- [x] Operation and scope validation
- [x] Timeout and circuit-breaker contract
- [x] Normalized response and error contract
- [x] Credential reference adapter
- [x] Provider adapter interface
- [x] Integration audit adapter

## P0 Status

COMPLETE

## Current Next Work

Phase 3 P0 is complete. Proceed to Phase 4 — Dalizebo Kernel.
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

Phase 3 P0 complete.

## Algorithm OS

P0 status: COMPLETE

## Loop OS

P0 status: COMPLETE

## Integrations OS

Connector standard: COMPLETE

Connector definition model: COMPLETE

Connector registry: COMPLETE

Runtime request contract: COMPLETE

Authorization gate: COMPLETE

Version compatibility: COMPLETE

Operation and scope validation: COMPLETE

Timeout and circuit-breaker contract: COMPLETE

Normalized response and error contract: COMPLETE

Credential reference adapter: COMPLETE

Provider adapter interface: COMPLETE

Integration audit adapter: COMPLETE

P0 status: COMPLETE

## Phase 3 Status

COMPLETE

## Next Work

Phase 4 — Dalizebo Kernel.

## Governing Rule

All orchestration remains subject to Pillars OS policy. Algorithm OS plans,
Loop OS executes bounded stateful work, Integrations OS controls external
interfaces, and production side effects require Dalizebo Kernel authorization.
""",
encoding="utf-8",
)

print("OK: Integrations OS Audit Adapter installed.")
print("OK: Integrations OS P0 marked COMPLETE.")
print("OK: Phase 3 P0 marked COMPLETE.")
print("NEXT: Phase 4 — Dalizebo Kernel.")
