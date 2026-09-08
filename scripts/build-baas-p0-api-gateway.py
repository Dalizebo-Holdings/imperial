#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"

required = [
    BAAS / "README.md",
    BAAS / "SERVICE_CONTRACT.md",
    BAAS / "api-gateway/README.md",
    BAAS / "api-gateway/GATEWAY_CONTRACT.md",
    BAAS / "api-gateway/runtime.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing API Gateway artifact: {path}"
        )

py_compile.compile(
    str(
        BAAS
        / "api-gateway/runtime.py"
    ),
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

## API Gateway P0 Components

- [x] /api/v1 route registry
- [x] Request validation
- [x] Authentication gate
- [x] Kernel authorization evidence gate
- [x] Permission evidence gate
- [x] Payload limits
- [x] Timeout budget
- [x] Reference rate-limit guard
- [x] Correlation/request identifiers
- [x] Safe structured errors
- [x] Dispatch plan
- [x] Audit/log context

## API Gateway Deferred Runtime

- [ ] Production reverse proxy adapter
- [ ] Distributed rate-limit adapter
- [ ] WAF/provider edge integration

## Current Next Work

Implement BaaS P0 Events service.
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

BaaS P0 API Gateway contract initialized.

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

/api/v1 route registry: COMPLETE

Authentication/authorization gates: COMPLETE

Request validation: COMPLETE

Payload limits: COMPLETE

Timeout budget: COMPLETE

Reference rate-limit guard: COMPLETE

Correlation/request IDs: COMPLETE

Safe structured errors: COMPLETE

Dispatch planning: COMPLETE

Production reverse proxy: DEFERRED

Distributed rate limiting: DEFERRED

## Next Work

BaaS P0 — Events service.

## Governing Rule

The API Gateway fails closed on invalid, unauthenticated, unauthorized,
oversized, unknown, disabled, or reference-rate-limited requests. It produces
safe dispatch metadata only; production network proxying and distributed rate
limiting remain adapter responsibilities.
""",
encoding="utf-8",
)

print("OK: API Gateway BaaS contract installed.")
print("OK: /api/v1 routing + auth/authz + validation gates installed.")
print("OK: Payload, timeout, reference rate-limit and safe errors installed.")
print("NEXT: BaaS P0 Events service.")
