#!/usr/bin/env python3

from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
KERNEL = ROOT / "kernel"

required = [
    KERNEL / "audit/README.md",
    KERNEL / "observability/README.md",
    KERNEL / "audit/PERSISTENCE.md",
    KERNEL / "errors/README.md",
    KERNEL / "observability/CONTRACT.md",
    KERNEL / "audit/persistence.py",
    KERNEL / "errors/runtime.py",
    KERNEL / "observability/logging.py",
    KERNEL / "observability/metrics.py",
    KERNEL / "observability/health.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Kernel observability artifact: {path}"
        )

for path in [
    KERNEL / "audit/persistence.py",
    KERNEL / "errors/runtime.py",
    KERNEL / "observability/logging.py",
    KERNEL / "observability/metrics.py",
    KERNEL / "observability/health.py",
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
- [ ] Secret reference boundary
- [ ] Backup contract
- [ ] Commerce primitives

## Current Next Work

Implement Kernel P0 secret reference boundary + backup contract.
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

Kernel P0 audit and observability contracts initialized.

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

## Next Work

Kernel P0 — secret reference boundary + backup contract.

## Governing Rule

Audit records remain separate from application logs. Every observable request
uses correlation IDs, logs redact secret/payment material, and authorization
or security failures fail closed.
""",
encoding="utf-8",
)

print("OK: Kernel tamper-evident audit persistence installed.")
print("OK: Kernel safe error contract installed.")
print("OK: Kernel structured logging/health/metrics contracts installed.")
print("NEXT: Secret reference boundary + backup contract.")
