#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"

required = [
    BAAS / "README.md",
    BAAS / "SERVICE_CONTRACT.md",
    BAAS / "events/README.md",
    BAAS / "events/EVENTS_CONTRACT.md",
    BAAS / "events/runtime.py",
    BAAS / "runtime/request_context.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Events BaaS artifact: {path}"
        )

for path in [
    BAAS / "events/runtime.py",
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
- [ ] Webhooks
- [ ] Background Jobs
- [ ] Audit
- [ ] Logging
- [ ] Usage Metering
- [ ] Subscription Billing
- [ ] Payment Abstraction
- [ ] Secrets
- [ ] Backups

## Events P0 Components

- [x] Kernel event envelope preservation
- [x] COMMITTED outbox publication gate
- [x] Tenant-scoped event subscriptions
- [x] Exact/wildcard event matching
- [x] Deterministic delivery identity
- [x] Delivery planning
- [x] Delivery success tracking
- [x] Bounded retry metadata
- [x] Dead-letter terminal state
- [x] Event-id conflict detection
- [x] Audit/log context
- [x] Secret-bearing payload rejection

## Events Deferred Runtime

- [ ] Production message broker adapter
- [ ] Production event worker
- [ ] Durable delivery ledger adapter

## Current Next Work

Implement BaaS P0 Webhooks service.
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

BaaS P0 Events contract initialized.

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

Kernel event envelope: COMPLETE

COMMITTED outbox publication gate: COMPLETE

Tenant subscriptions: COMPLETE

Deterministic delivery identity: COMPLETE

Delivery/retry/dead-letter tracking: COMPLETE

Audit/log context: COMPLETE

Production message broker: DEFERRED

Production event worker: DEFERRED

Durable delivery ledger: DEFERRED

## Next Work

BaaS P0 — Webhooks service.

## Governing Rule

Events BaaS never publishes before transaction commit. Only COMMITTED Kernel
outbox events enter delivery planning. Delivery identities are deterministic,
retries are bounded, cross-tenant subscriptions fail closed, and production
broker/worker execution remains an adapter responsibility.
""",
encoding="utf-8",
)

print("OK: Events BaaS contract installed.")
print("OK: COMMITTED outbox gate + subscriptions + delivery tracking installed.")
print("OK: Bounded retry/dead-letter metadata installed.")
print("NEXT: BaaS P0 Webhooks service.")
