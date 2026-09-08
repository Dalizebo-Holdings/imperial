#!/usr/bin/env python3

from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
KERNEL = ROOT / "kernel"

required = [
    KERNEL / "README.md",
    KERNEL / "ARCHITECTURE.md",
    KERNEL / "identity/README.md",
    KERNEL / "tenancy/README.md",
    KERNEL / "authorization/README.md",
    KERNEL / "identity/CONTEXT.md",
    KERNEL / "tenancy/RUNTIME.md",
    KERNEL / "authorization/RUNTIME.md",
    KERNEL / "identity/context.py",
    KERNEL / "tenancy/context.py",
    KERNEL / "authorization/runtime.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Kernel P0 artifact: {path}"
        )

for path in [
    KERNEL / "identity/context.py",
    KERNEL / "tenancy/context.py",
    KERNEL / "authorization/runtime.py",
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
- [ ] Shared identifier runtime
- [ ] Transaction utilities
- [ ] Idempotency runtime
- [ ] Kernel audit persistence
- [ ] Error contract
- [ ] Structured logging
- [ ] Health checks
- [ ] Metrics
- [ ] Secret reference boundary
- [ ] Backup contract
- [ ] Commerce primitives

## Current Next Work

Implement Kernel P0 shared identifiers + transaction/idempotency primitives.
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

Kernel P0 trust boundary initialized.

## Identity

Identity context: COMPLETE

## Tenancy

Verified tenant context: COMPLETE

Tenant hierarchy enforcement: COMPLETE

Cross-tenant detection: COMPLETE

## Authorization

Permission registry: COMPLETE

Role registry: COMPLETE

RBAC evaluation: COMPLETE

Policy gate: COMPLETE

Privileged cross-tenant rule: COMPLETE

Deterministic authorization reference: COMPLETE

Authorization audit event: COMPLETE

## Next Work

Kernel P0 — shared identifiers + transaction/idempotency primitives.

## Governing Rule

Kernel authorization fails closed. No production side effect may bypass verified
identity, tenant context, permission evaluation, upstream policy approval, and
Kernel authorization.
""",
encoding="utf-8",
)

print("OK: Kernel identity context initialized.")
print("OK: Kernel verified tenant context initialized.")
print("OK: Kernel RBAC authorization boundary initialized.")
print("NEXT: Shared identifiers + transaction/idempotency primitives.")
