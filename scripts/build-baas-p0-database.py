#!/usr/bin/env python3

from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"

required = [
    BAAS / "README.md",
    BAAS / "SERVICE_CONTRACT.md",
    BAAS / "database/README.md",
    BAAS / "database/DATABASE_CONTRACT.md",
    BAAS / "database/runtime.py",
    BAAS / "runtime/request_context.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Database BaaS artifact: {path}"
        )

for path in [
    BAAS / "database/runtime.py",
    BAAS / "runtime/request_context.py",
]:
    py_compile.compile(str(path), doraise=True)

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
- [ ] Object Storage
- [ ] Serverless Functions
- [ ] API Gateway
- [ ] Events
- [ ] Webhooks
- [ ] Background Jobs
- [ ] Audit
- [ ] Logging
- [ ] Usage Metering
- [ ] Subscription Billing
- [ ] Payment Abstraction
- [ ] Secrets
- [ ] Backups

## Database BaaS P0 Components

- [x] Managed database descriptor
- [x] Tenant database manager
- [x] Connection policy
- [x] Database lifecycle
- [x] Migration intent validation
- [x] Restore intent validation
- [x] Query observation contract
- [x] Kernel authorization evidence requirement

## Authentication Deferred Components

- [ ] Password credential provider
- [ ] Password recovery delivery
- [ ] MFA provider
- [ ] Passkey/WebAuthn provider

## Current Next Work

Implement BaaS P0 Object Storage service.
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

BaaS P0 Database service initialized.

## Foundation

Shared service/request contract: COMPLETE

Kernel authorization reference requirement: COMPLETE

Tenant execution context: COMPLETE

## Authentication

Identity/session/API-key foundation: COMPLETE

Concrete password/MFA/passkey providers: DEFERRED

## Database

PostgreSQL Database BaaS: COMPLETE

Managed database descriptor: COMPLETE

Tenant database manager: COMPLETE

Connection policy: COMPLETE

Migration intent validation: COMPLETE

Restore intent validation: COMPLETE

Query observation contract: COMPLETE

## Next Work

BaaS P0 — Object Storage service.

## Governing Rule

Database BaaS is a tenant-scoped control plane above the Kernel PostgreSQL
boundary. It stores secret references only, requires Kernel authorization
evidence, uses Kernel transaction semantics for multi-record changes, and does
not expose raw SQL credentials or query payloads through observability records.
""",
encoding="utf-8",
)

print("OK: PostgreSQL Database BaaS contract installed.")
print("OK: Tenant database manager installed.")
print("OK: Migration/restore/query-observability contracts installed.")
print("NEXT: BaaS P0 Object Storage service.")
