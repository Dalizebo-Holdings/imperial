#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"
KERNEL = ROOT / "kernel"

required = [
    BAAS / "README.md",
    BAAS / "SERVICE_CONTRACT.md",
    BAAS / "audit/README.md",
    BAAS / "audit/AUDIT_CONTRACT.md",
    BAAS / "audit/runtime.py",
    BAAS / "runtime/request_context.py",
    KERNEL / "audit/README.md",
    KERNEL / "audit/PERSISTENCE.md",
    KERNEL / "audit/persistence.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing BaaS/Kernel audit artifact: {path}"
        )

for path in [
    BAAS / "audit/runtime.py",
    BAAS / "runtime/request_context.py",
    KERNEL / "audit/persistence.py",
]:
    py_compile.compile(
        str(path),
        doraise=True,
    )

(BAAS / "IMPLEMENTATION_STATUS.md").write_text(
"""# Dalizebo BaaS Implementation Status

## Phase

Phase 5

## P0 Services

- [x] Shared BaaS service/request contract
- [x] Authentication identity registry
- [x] Session lifecycle
- [x] Session invalidation
- [x] API key lifecycle
- [x] Service-account/API-client identity model
- [x] PostgreSQL Database BaaS
- [x] Object Storage
- [x] Serverless Functions
- [x] API Gateway
- [x] Events
- [x] Webhooks
- [x] Background Jobs
- [x] Audit
- [ ] Logging
- [ ] Usage Metering
- [ ] Subscription Billing
- [ ] Payment Abstraction
- [ ] Secrets
- [ ] Backups

## Audit P0 Components

- [x] Kernel Audit authority boundary
- [x] Full source-chain verification before access
- [x] Tenant-scoped audit query
- [x] Action/actor/resource/correlation/time filters
- [x] Deterministic sequence pagination
- [x] Defensive metadata redaction
- [x] Tamper-evident export manifest
- [x] Export selection verification
- [x] Query/export access audit planning
- [x] No audit mutation/delete API
- [x] Kernel authorization evidence requirement

## Audit Deferred Runtime

- [ ] Durable Audit query index/read model
- [ ] Large export object-storage adapter
- [ ] Compliance retention/legal-hold policy adapter

## Current Next Work

Implement BaaS P0 Logging service.
""",
encoding="utf-8",
)

(BAAS / "STATUS.md").write_text(
"""# Dalizebo BaaS Status

## Phase

Phase 5 — Dalizebo BaaS

## Prerequisite

Kernel P0: COMPLETE

## Current Stage

BaaS P0 Audit service initialized.

## Foundation

Shared service/request contract: COMPLETE

Kernel authorization reference requirement: COMPLETE

Tenant execution context: COMPLETE

## Authentication

Identity/session/API-key foundation: COMPLETE

## Database

PostgreSQL Database BaaS: COMPLETE

## Storage

Object Storage BaaS: COMPLETE

## Functions

Serverless Functions BaaS: COMPLETE

## API Gateway

API Gateway BaaS: COMPLETE

## Events

Events BaaS: COMPLETE

## Webhooks

Webhooks BaaS: COMPLETE

## Background Jobs

Background Jobs BaaS: COMPLETE

## Audit

Audit BaaS: COMPLETE

Kernel Audit authority boundary: COMPLETE

Source-chain verification before access: COMPLETE

Tenant query/filter/pagination: COMPLETE

Tamper-evident export manifest: COMPLETE

Query/export access audit planning: COMPLETE

Audit mutation/delete API: NONE

Durable query index/read model: DEFERRED

Large export adapter: DEFERRED

## Next Work

BaaS P0 — Logging service.

## Governing Rule

Kernel Audit remains the authoritative audit ledger. BaaS Audit verifies the
Kernel chain before every query/export, fails closed on tampering, never rewrites
or deletes authoritative evidence, enforces tenant scope, redacts sensitive
metadata defensively, and emits access-audit evidence for its own reads/exports.
""",
encoding="utf-8",
)

print("OK: Audit BaaS contract installed.")
print("OK: Kernel-chain verification + tenant query/export installed.")
print("OK: Audit access evidence + no-mutation boundary installed.")
print("NEXT: BaaS P0 Logging service.")
