#!/usr/bin/env python3

from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
INTEGRATIONS = ROOT / "orchestration/integrations-os"
RUNTIME = INTEGRATIONS / "runtime"

required = [
    INTEGRATIONS / "CREDENTIAL_REFERENCE_ADAPTER.md",
    INTEGRATIONS / "PROVIDER_ADAPTER_INTERFACE.md",
    RUNTIME / "connector_model.py",
    RUNTIME / "connector_registry.py",
    RUNTIME / "runtime_contract.py",
    RUNTIME / "credential_reference.py",
    RUNTIME / "provider_adapter.py",
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
- [ ] Integration audit adapter

## Current Next Work

Implement Integrations OS P0 Audit Adapter, then close Integrations OS P0 and Phase 3 P0.
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

Integrations OS P0 credential and provider boundaries complete.

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

Integration audit adapter: PENDING

## Next Work

Integrations OS P0 — Audit Adapter.

## Governing Rule

Integrations OS stores credential references only. Raw provider secrets remain
outside orchestration runtime objects. External execution still requires
Algorithm OS planning, Pillars OS approval, Dalizebo Kernel authorization,
bounded Loop OS execution, and a registered provider adapter.
""",
encoding="utf-8",
)

print("OK: Credential Reference Adapter installed.")
print("OK: Provider Adapter Interface installed.")
print("NEXT: Integrations OS P0 Audit Adapter.")
