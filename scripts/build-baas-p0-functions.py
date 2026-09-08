#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"

required = [
    BAAS / "README.md",
    BAAS / "SERVICE_CONTRACT.md",
    BAAS / "functions/README.md",
    BAAS / "functions/FUNCTIONS_CONTRACT.md",
    BAAS / "functions/runtime.py",
    BAAS / "runtime/request_context.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Functions BaaS artifact: {path}"
        )

for path in [
    BAAS / "functions/runtime.py",
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

## Functions P0 Components

- [x] Tenant function descriptor
- [x] HTTP trigger contract
- [x] Event trigger contract
- [x] Scheduled trigger metadata contract
- [x] Manual trigger contract
- [x] Bounded timeout and memory policy
- [x] Secret reference injection contract
- [x] Function lifecycle
- [x] Invocation plan
- [x] Audit/log context
- [x] Kernel authorization evidence requirement

## Functions Deferred Runtime

- [ ] Isolated production code executor
- [ ] Production scheduler adapter
- [ ] Network egress policy adapter
- [ ] Provider-native secret injection adapter

## Current Next Work

Implement BaaS P0 API Gateway service.
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

BaaS P0 Serverless Functions contract initialized.

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

Tenant function descriptor: COMPLETE

Bounded timeout/memory policy: COMPLETE

HTTP/event/scheduled/manual trigger contracts: COMPLETE

Secret reference injection contract: COMPLETE

Invocation planning: COMPLETE

Audit/log context: COMPLETE

Production code executor: DEFERRED

Production scheduler adapter: DEFERRED

## Next Work

BaaS P0 — API Gateway service.

## Governing Rule

Functions BaaS P0 manages definitions and produces bounded, tenant-scoped,
Kernel-authorized invocation plans. It does not execute arbitrary code.
Production execution must occur through an isolated runtime adapter with
resource limits, secret injection at execution time, structured logs, and
audit evidence.
""",
encoding="utf-8",
)

print("OK: Serverless Functions BaaS contract installed.")
print("OK: Tenant function lifecycle + invocation planning installed.")
print("OK: Bounded resources, secret references and audit/log context installed.")
print("NEXT: BaaS P0 API Gateway service.")
