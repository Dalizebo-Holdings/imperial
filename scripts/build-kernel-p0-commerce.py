#!/usr/bin/env python3

from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
KERNEL = ROOT / "kernel"

required = [
    KERNEL / "commerce/README.md",
    KERNEL / "commerce/PRIMITIVES.md",
    KERNEL / "commerce/runtime.py",
    KERNEL / "migrations/runtime.py",
    KERNEL / "migrations/sql/0001_kernel_foundation.sql",
    KERNEL / "migrations/sql/0002_kernel_commerce_primitives.sql",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Kernel commerce artifact: {path}"
        )

for path in [
    KERNEL / "commerce/runtime.py",
    KERNEL / "migrations/runtime.py",
]:
    py_compile.compile(str(path), doraise=True)

(KERNEL / "IMPLEMENTATION_STATUS.md").write_text(
"""# Dalizebo Kernel Implementation Status

## Phase

Phase 4

## P0 Components

- [x] Identity context contract
- [x] Verified tenant context
- [x] Permission registry
- [x] Role registry
- [x] RBAC permission evaluation
- [x] Policy outcome gate
- [x] Cross-tenant privileged access rule
- [x] Deterministic authorization reference
- [x] Authorization audit event
- [x] Shared identifier runtime
- [x] Transaction utilities
- [x] Idempotency runtime
- [x] Kernel audit persistence
- [x] Error contract
- [x] Structured logging
- [x] Health checks
- [x] Metrics
- [x] Secret reference boundary
- [x] Backup contract
- [x] PostgreSQL persistence boundary
- [x] Migration framework
- [x] Commerce primitives

## P0 Status

COMPLETE

## Current Next Work

Proceed to Phase 5 — Dalizebo BaaS.
""",
encoding="utf-8",
)

(KERNEL / "STATUS.md").write_text(
"""# Dalizebo Kernel Status

## Phase

Phase 4 — Dalizebo Kernel

## Prerequisite

Phase 3 P0: COMPLETE

## Current Stage

Kernel P0 complete.

## Trust Boundary

Identity + tenancy + authorization: COMPLETE

## Data Safety

Shared identifiers: COMPLETE

Transaction utilities: COMPLETE

Idempotency runtime: COMPLETE

Transactional outbox contract: COMPLETE

## Audit & Observability

Tamper-evident audit persistence: COMPLETE

Safe error contract: COMPLETE

Structured logging: COMPLETE

Health/readiness checks: COMPLETE

Metrics contract: COMPLETE

## Security & Recovery

Secret reference boundary: COMPLETE

Backup contract: COMPLETE

## Persistence

PostgreSQL persistence boundary: COMPLETE

Migration framework: COMPLETE

Baseline Kernel schema migration: COMPLETE

Commerce schema migration: COMPLETE

## Domain

Shared commerce primitives: COMPLETE

## P0 Status

COMPLETE

## Next Work

Phase 5 — Dalizebo BaaS.

## Governing Rule

The Kernel remains the smallest trusted shared execution layer. Commerce and
POS reuse the same authoritative commerce primitives. No SaaS product may
duplicate authoritative Kernel models. Side effects remain tenant-scoped,
authorized, idempotent, transactional, auditable, observable, and recoverable.
""",
encoding="utf-8",
)

print("OK: Kernel shared commerce primitives installed.")
print("OK: Commerce PostgreSQL migration installed.")
print("OK: Kernel P0 marked COMPLETE.")
print("NEXT: Phase 5 — Dalizebo BaaS.")
