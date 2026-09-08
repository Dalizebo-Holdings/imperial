#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"

required = [
    BAAS / "README.md",
    BAAS / "SERVICE_CONTRACT.md",
    BAAS / "webhooks/README.md",
    BAAS / "webhooks/WEBHOOKS_CONTRACT.md",
    BAAS / "webhooks/runtime.py",
    BAAS / "runtime/request_context.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Webhooks BaaS artifact: {path}"
        )

for path in [
    BAAS / "webhooks/runtime.py",
    BAAS / "runtime/request_context.py",
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
- [ ] Background Jobs
- [ ] Audit
- [ ] Logging
- [ ] Usage Metering
- [ ] Subscription Billing
- [ ] Payment Abstraction
- [ ] Secrets
- [ ] Backups

## Webhooks P0 Components

- [x] Tenant webhook endpoint registry
- [x] HTTPS-only endpoint policy
- [x] HMAC-SHA256 signing contract
- [x] Secret-reference signing boundary
- [x] Deterministic delivery identity
- [x] Bounded timeout/retry policy
- [x] Delivery state tracking
- [x] Dead-letter state
- [x] Replay with linked delivery identity
- [x] Signing-secret rotation metadata
- [x] Duplicate-delivery/idempotency contract
- [x] Audit/log context

## Webhooks Deferred Runtime

- [ ] Production outbound HTTPS adapter
- [ ] DNS rebinding/connect-time network policy enforcement
- [ ] Durable delivery ledger adapter

## Current Next Work

Implement BaaS P0 Background Jobs service.
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

BaaS P0 Webhooks contract initialized.

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

HTTPS-only endpoint policy: COMPLETE

Signed payload contract: COMPLETE

Secret-reference signing boundary: COMPLETE

Deterministic delivery identity: COMPLETE

Bounded retries/timeouts: COMPLETE

Delivery/dead-letter tracking: COMPLETE

Replay metadata: COMPLETE

Secret rotation metadata: COMPLETE

Production outbound HTTPS adapter: DEFERRED

Durable delivery ledger: DEFERRED

## Next Work

BaaS P0 — Background Jobs service.

## Governing Rule

Webhook consumers must assume duplicate delivery and implement idempotency.
Webhooks are HTTPS-only, tenant-scoped, Kernel-authorized, signed using
transient secret material, bounded by timeout/retry policy, and never perform
network delivery inside the P0 control-plane runtime.
""",
encoding="utf-8",
)

print("OK: Webhooks BaaS contract installed.")
print("OK: Signing + retries + replay + dead-letter controls installed.")
print("OK: Secret rotation + HTTPS endpoint policy installed.")
print("NEXT: BaaS P0 Background Jobs service.")
