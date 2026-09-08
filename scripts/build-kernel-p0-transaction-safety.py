#!/usr/bin/env python3

from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
KERNEL = ROOT / "kernel"

required = [
    KERNEL / "data/DATA_MODEL.md",
    KERNEL / "idempotency/README.md",
    KERNEL / "events/README.md",
    KERNEL / "data/IDENTIFIERS.md",
    KERNEL / "transactions/README.md",
    KERNEL / "idempotency/RUNTIME.md",
    KERNEL / "data/identifiers.py",
    KERNEL / "transactions/runtime.py",
    KERNEL / "idempotency/runtime.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Kernel P0 primitive artifact: {path}"
        )

for path in [
    KERNEL / "data/identifiers.py",
    KERNEL / "transactions/runtime.py",
    KERNEL / "idempotency/runtime.py",
]:
    py_compile.compile(str(path), doraise=True)

status_path = KERNEL / "IMPLEMENTATION_STATUS.md"

status_path.write_text(
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
- [ ] Kernel audit persistence
- [ ] Error contract
- [ ] Structured logging
- [ ] Health checks
- [ ] Metrics
- [ ] Secret reference boundary
- [ ] Backup contract
- [ ] Commerce primitives

## Current Next Work

Implement Kernel P0 audit persistence + error/observability contracts.
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

Kernel P0 transaction safety primitives initialized.

## Trust Boundary

Identity + tenancy + authorization: COMPLETE

## Data Safety

Shared identifiers: COMPLETE

Transaction utilities: COMPLETE

Idempotency runtime: COMPLETE

Transactional outbox contract: COMPLETE

## Next Work

Kernel P0 — audit persistence + error/observability contracts.

## Governing Rule

Kernel state changes requiring atomicity must commit business state, audit
evidence, and outbox events together. Idempotent operations reject reuse of the
same key with a different request hash. Events are never publishable before
transaction commit.
""",
encoding="utf-8",
)

print("OK: Kernel shared identifier runtime installed.")
print("OK: Kernel transaction utilities installed.")
print("OK: Kernel idempotency runtime installed.")
print("NEXT: Audit persistence + error/observability contracts.")
