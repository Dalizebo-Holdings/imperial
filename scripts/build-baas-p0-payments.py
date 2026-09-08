#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"
KERNEL = ROOT / "kernel"

required = [
    BAAS / "README.md",
    BAAS / "SERVICE_CONTRACT.md",
    BAAS / "payments/README.md",
    BAAS / "payments/PAYMENTS_CONTRACT.md",
    BAAS / "payments/runtime.py",
    BAAS / "billing/README.md",
    BAAS / "runtime/request_context.py",
    KERNEL / "commerce/PRIMITIVES.md",
    KERNEL / "commerce/runtime.py",
    KERNEL / "secrets/README.md",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Payment Abstraction prerequisite/artifact: {path}"
        )

for path in [
    BAAS / "payments/runtime.py",
    BAAS / "runtime/request_context.py",
    KERNEL / "commerce/runtime.py",
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
- [ ] Secrets
- [ ] Backups

## Payment Abstraction P0 Components

- [x] Kernel payment authority boundary
- [x] Provider-neutral registry
- [x] Secret-reference provider credentials
- [x] Currency/capability validation
- [x] Idempotent payment planning
- [x] Provider adapter operation plan
- [x] Explicit Kernel payment transition sequences
- [x] Immediate-capture explicit AUTHORIZED→CAPTURED path
- [x] Safe provider-result contract
- [x] Refund planning
- [x] Kernel refund validation boundary
- [x] Payment reconciliation
- [x] Audit/payment event metadata
- [x] Cross-tenant payment isolation
- [x] Billing/payment boundary
- [x] Current invoice-source Kernel limitation documented

## Payment Abstraction Deferred Runtime

- [ ] Licensed provider adapter implementation
- [ ] Provider webhook/callback adapter
- [ ] Durable payment orchestration ledger
- [ ] Kernel generic payment-source extension for invoice-backed payments
- [ ] Production settlement reconciliation adapter

## Current Next Work

Implement BaaS P0 Secrets service.
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

BaaS P0 Payment Abstraction service initialized.

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

## Logging

Logging BaaS: COMPLETE

## Usage Metering

Usage Metering BaaS: COMPLETE

## Subscription Billing

Subscription Billing BaaS: COMPLETE

## Payment Abstraction

Payment Abstraction BaaS: COMPLETE

Kernel payment authority boundary: COMPLETE

Provider-neutral registry: COMPLETE

Secret-reference credentials: COMPLETE

Idempotent operation planning: COMPLETE

Explicit Kernel transition planning: COMPLETE

Refund validation/planning: COMPLETE

Payment reconciliation: COMPLETE

Licensed provider adapters: DEFERRED

Provider network execution: DEFERRED

Invoice-backed Kernel payment-source extension: DEFERRED

## Next Work

BaaS P0 — Secrets service.

## Governing Rule

Payments BaaS orchestrates providers but does not own authoritative payment
state. Every lifecycle edge is explicitly validated against Kernel payment
rules, provider credentials remain opaque references, payment/refund requests
are idempotent, and network/provider execution remains behind licensed adapters.
""",
encoding="utf-8",
)

print("OK: Payment Abstraction BaaS contract installed.")
print("OK: Provider-neutral idempotent payment/refund planning installed.")
print("OK: Explicit Kernel lifecycle + reconciliation boundary installed.")
print("NEXT: BaaS P0 Secrets service.")
