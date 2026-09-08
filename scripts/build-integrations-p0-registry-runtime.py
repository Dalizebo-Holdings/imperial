#!/usr/bin/env python3

from pathlib import Path
import json
import py_compile

ROOT = Path(__file__).resolve().parent.parent
INTEGRATIONS = ROOT / "orchestration/integrations-os"
RUNTIME = INTEGRATIONS / "runtime"

required = [
    INTEGRATIONS / "README.md",
    INTEGRATIONS / "CONNECTOR_STANDARD.md",
    INTEGRATIONS / "CONNECTOR_REGISTRY.md",
    INTEGRATIONS / "RUNTIME_CONTRACT.md",
    RUNTIME / "connector_model.py",
    RUNTIME / "connector_registry.py",
    RUNTIME / "runtime_contract.py",
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
]:
    py_compile.compile(str(path), doraise=True)

categories = [
    "Payments",
    "Banking",
    "Accounting",
    "Email",
    "SMS",
    "WhatsApp",
    "Logistics",
    "E-commerce",
    "Cloud",
    "Developer tools",
    "Analytics",
    "Government services",
    "IoT",
]

(INTEGRATIONS / "connector-categories.json").write_text(
    json.dumps(
        {
            "version": "phase3-integrations-categories-v1",
            "categories": categories,
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

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
- [ ] Credential reference adapter
- [ ] Provider adapter interface
- [ ] Integration audit adapter

## Current Next Work

Implement Integrations OS P0 credential reference adapter + provider adapter interface.
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

Integrations OS P0 registry and runtime contracts complete.

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

Credential reference adapter: PENDING

Provider adapter interface: PENDING

Integration audit adapter: PENDING

## Next Work

Integrations OS P0 — credential reference adapter + provider adapter interface.

## Governing Rule

Integrations OS stores no raw provider secrets and performs no external side
effects without Algorithm OS planning, Pillars OS approval, Dalizebo Kernel
authorization, and bounded Loop OS execution.
""",
encoding="utf-8",
)

print("OK: Integrations OS connector registry initialized.")
print("OK: Integrations OS runtime contracts initialized.")
print("NEXT: Credential reference adapter + provider adapter interface.")
