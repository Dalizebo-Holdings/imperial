#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"
KERNEL = ROOT / "kernel"

required = [
    BAAS / "README.md",
    BAAS / "SERVICE_CONTRACT.md",
    BAAS / "billing/README.md",
    BAAS / "billing/BILLING_CONTRACT.md",
    BAAS / "billing/runtime.py",
    BAAS / "metering/README.md",
    BAAS / "metering/runtime.py",
    BAAS / "payments/README.md",
    BAAS / "runtime/request_context.py",
    KERNEL / "commerce/PRIMITIVES.md",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Billing prerequisite/artifact: {path}"
        )

for path in [
    BAAS / "billing/runtime.py",
    BAAS / "metering/runtime.py",
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
- [ ] Payment Abstraction
- [ ] Secrets
- [ ] Backups

## Subscription Billing P0 Components

- [x] Immutable versioned plan pricing
- [x] Subscription lifecycle
- [x] Subscription + metered-usage billing model
- [x] Integer minor-unit money
- [x] Decimal usage rating with explicit rounding
- [x] Usage Metering aggregate evidence boundary
- [x] Tenant-safe credits
- [x] Deterministic invoice generation
- [x] Draft/open invoice lifecycle
- [x] Pricing-version retention on invoices
- [x] Entitlement resolution
- [x] Billing event metadata
- [x] Payment retry intent metadata
- [x] Payment-provider execution boundary
- [x] Invoice/source-hash reconciliation
- [x] Kernel authorization evidence requirement

## Subscription Billing Deferred Runtime

- [ ] Durable billing ledger adapter
- [ ] Tax engine
- [ ] Proration engine
- [ ] Dunning scheduler
- [ ] Invoice document renderer
- [ ] Provider payment execution

## Current Next Work

Implement BaaS P0 Payment Abstraction service.
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

BaaS P0 Subscription Billing service initialized.

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

Versioned plan pricing: COMPLETE

Subscription lifecycle: COMPLETE

Recurring + metered rating: COMPLETE

Integer minor-unit money: COMPLETE

Credits: COMPLETE

Deterministic invoices: COMPLETE

Entitlement resolution: COMPLETE

Billing events: COMPLETE

Payment retry intents: COMPLETE

Invoice reconciliation: COMPLETE

Provider payment execution: DEFERRED

Tax/proration/dunning/document rendering: DEFERRED

## Next Work

BaaS P0 — Payment Abstraction service.

## Governing Rule

Billing consumes immutable Usage Metering aggregate evidence and exact versioned
pricing. Money is integer minor units, invoices are deterministic and
reconcilable, credits cannot make totals negative, and payment retry output is
intent metadata only. Provider charging and payment state transitions remain
behind Payments BaaS and Kernel commerce invariants.
""",
encoding="utf-8",
)

print("OK: Subscription Billing BaaS contract installed.")
print("OK: Versioned pricing + recurring/metered rating + invoices installed.")
print("OK: Credits, entitlements, reconciliation and payment-retry boundary installed.")
print("NEXT: BaaS P0 Payment Abstraction service.")
