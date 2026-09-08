#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"
KERNEL = ROOT / "kernel"

required = [
    BAAS / "README.md",
    BAAS / "SERVICE_CONTRACT.md",
    BAAS / "backups/README.md",
    BAAS / "backups/BACKUPS_CONTRACT.md",
    BAAS / "backups/runtime.py",
    BAAS / "runtime/request_context.py",
    KERNEL / "backups/README.md",
    KERNEL / "backups/runtime.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Backups prerequisite/artifact: {path}"
        )

for path in [
    BAAS / "backups/runtime.py",
    BAAS / "runtime/request_context.py",
    KERNEL / "backups/runtime.py",
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
- [x] Logging
- [x] Usage Metering
- [x] Subscription Billing
- [x] Payment Abstraction
- [x] Secrets
- [x] Backups

## Backups P0 Components

- [x] Kernel Backup authority boundary
- [x] Tenant/resource backup policies
- [x] Provider-neutral backup registry
- [x] Secret-reference provider credentials
- [x] Production encryption/immutable/offsite requirements
- [x] Retention/frequency/RPO/RTO policy
- [x] Automated-backup due calculation
- [x] Backup execution planning
- [x] Strict opaque backup references
- [x] Timezone-aware backup evidence
- [x] Successful-backup checksum requirement
- [x] Restore-test planning
- [x] Restore verification through Kernel registry
- [x] Secret-safe restore notes
- [x] Restore-test staleness enforcement
- [x] Trusted recovery gate
- [x] Restore execution planning
- [x] Audit evidence
- [x] Kernel authorization evidence requirement

## Backups Deferred Runtime

- [ ] Production PostgreSQL backup/PITR adapter
- [ ] Production object-storage backup adapter
- [ ] Cross-region/immutable-copy provider adapter
- [ ] Restore executor
- [ ] Backup scheduler
- [ ] Operational RPO/RTO measurement

## Phase 5 P0 Result

DALIZEBO BAAS P0: COMPLETE

## Current Next Work

Phase 6 — Commerce + POS foundation.
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

Dalizebo BaaS P0 complete.

## P0 Services

Authentication: COMPLETE

PostgreSQL Database: COMPLETE

Object Storage: COMPLETE

Serverless Functions: COMPLETE

API Gateway: COMPLETE

Events: COMPLETE

Webhooks: COMPLETE

Background Jobs: COMPLETE

Audit: COMPLETE

Logging: COMPLETE

Usage Metering: COMPLETE

Subscription Billing: COMPLETE

Payment Abstraction: COMPLETE

Secrets: COMPLETE

Backups: COMPLETE

## Backups

Kernel Backup authority boundary: COMPLETE

Tenant/resource policy: COMPLETE

Production encryption/immutable/offsite rules: COMPLETE

Retention/frequency/RPO/RTO: COMPLETE

Automated-backup due calculation: COMPLETE

Backup evidence: COMPLETE

Restore testing: COMPLETE

Restore-test staleness enforcement: COMPLETE

Trusted recovery gate: COMPLETE

Restore planning: COMPLETE

Provider execution: DEFERRED

Operational RPO/RTO measurement: DEFERRED

## Phase 5 Result

DALIZEBO BAAS P0: COMPLETE

## Next Work

Phase 6 — Commerce + POS foundation.

## Governing Rule

Dalizebo BaaS extends the Kernel without replacing Kernel authority. Backup and
restore operations remain provider-neutral and adapter-driven; production
backups are not trusted until restoration has been successfully verified within
the configured restore-test interval. All BaaS P0 service boundaries remain
tenant-scoped, Kernel-authorized, auditable, and reference-safe.
""",
encoding="utf-8",
)

print("OK: Backups BaaS contract installed.")
print("OK: Backup policy/evidence + restore trust/plan controls installed.")
print("OK: Restore-test staleness hardening installed.")
print("STATUS: DALIZEBO BAAS P0 COMPLETE")
print("NEXT: Phase 6 — Commerce + POS foundation.")
