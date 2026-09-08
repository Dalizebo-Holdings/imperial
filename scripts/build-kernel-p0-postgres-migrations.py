#!/usr/bin/env python3

from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
KERNEL = ROOT / "kernel"

required = [
    KERNEL / "ARCHITECTURE.md",
    KERNEL / "data/DATA_MODEL.md",
    KERNEL / "persistence/POSTGRESQL.md",
    KERNEL / "persistence/runtime.py",
    KERNEL / "migrations/README.md",
    KERNEL / "migrations/runtime.py",
    KERNEL / "migrations/sql/0001_kernel_foundation.sql",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Kernel PostgreSQL/migration artifact: {path}"
        )

for path in [
    KERNEL / "persistence/runtime.py",
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
- [ ] Commerce primitives

## Current Next Work

Implement Kernel P0 commerce primitives, then close Kernel P0.
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

Kernel P0 PostgreSQL persistence and migrations initialized.

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

## Domain

Commerce primitives: PENDING

## Next Work

Kernel P0 — commerce primitives.

## Governing Rule

PostgreSQL credentials remain behind secret references. Tenant-aware database
work executes inside explicit transactions with transaction-local tenant
context. Migration history is ordered and checksummed; checksum drift fails
closed. Business state, audit evidence, and outbox rows remain atomic.
""",
encoding="utf-8",
)

print("OK: Kernel PostgreSQL persistence boundary installed.")
print("OK: Kernel migration framework installed.")
print("OK: Baseline Kernel PostgreSQL schema migration installed.")
print("NEXT: Kernel P0 commerce primitives.")
