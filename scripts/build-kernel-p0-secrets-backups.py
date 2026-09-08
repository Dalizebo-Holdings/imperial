#!/usr/bin/env python3

from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
KERNEL = ROOT / "kernel"

required = [
    KERNEL / "README.md",
    KERNEL / "ARCHITECTURE.md",
    KERNEL / "secrets/README.md",
    KERNEL / "backups/README.md",
    KERNEL / "secrets/runtime.py",
    KERNEL / "backups/runtime.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Kernel secret/backup artifact: {path}"
        )

for path in [
    KERNEL / "secrets/runtime.py",
    KERNEL / "backups/runtime.py",
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
- [ ] PostgreSQL persistence boundary
- [ ] Migration framework
- [ ] Commerce primitives

## Current Next Work

Implement Kernel P0 PostgreSQL persistence boundary + migration framework.
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

Kernel P0 secret and recovery boundaries initialized.

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

PostgreSQL persistence boundary: PENDING

Migration framework: PENDING

## Domain

Commerce primitives: PENDING

## Next Work

Kernel P0 — PostgreSQL persistence boundary + migration framework.

## Governing Rule

Kernel stores secret references only, not raw secret values. Production backup
policies require encryption, immutable and offsite copies, and auditable restore
verification. Kernel P0 cannot close until the PostgreSQL/migration requirements
from the canonical Kernel architecture are implemented.
""",
encoding="utf-8",
)

print("OK: Kernel secret reference boundary installed.")
print("OK: Kernel backup/recovery contract installed.")
print("OK: PostgreSQL + migration requirements restored to P0 checklist.")
print("NEXT: PostgreSQL persistence boundary + migration framework.")
