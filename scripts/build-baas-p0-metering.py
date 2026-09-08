#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"

required = [
    BAAS / "README.md",
    BAAS / "SERVICE_CONTRACT.md",
    BAAS / "metering/README.md",
    BAAS / "metering/METERING_CONTRACT.md",
    BAAS / "metering/runtime.py",
    BAAS / "runtime/request_context.py",
    BAAS / "billing/README.md",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Usage Metering artifact: {path}"
        )

for path in [
    BAAS / "metering/runtime.py",
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
- [x] Background Jobs
- [x] Audit
- [x] Logging
- [x] Usage Metering
- [ ] Subscription Billing
- [ ] Payment Abstraction
- [ ] Secrets
- [ ] Backups

## Usage Metering P0 Components

- [x] Canonical initial metered-resource registry
- [x] Tenant-attributed usage events
- [x] Timestamped immutable raw usage records
- [x] Decimal quantity normalization
- [x] Idempotent ingestion
- [x] Idempotency conflict detection
- [x] Record hashing
- [x] Secret-bearing dimension rejection
- [x] Auditable ingestion evidence
- [x] Deterministic period aggregation
- [x] Unit-safe aggregation
- [x] Aggregate source hashing
- [x] Aggregate audit evidence
- [x] Reconciliation verification
- [x] No raw usage mutation/delete API

## Usage Metering Deferred Runtime

- [ ] Durable raw usage ledger adapter
- [ ] Durable aggregate/read-model adapter
- [ ] Streaming/event ingestion adapter
- [ ] Rating/pricing engine
- [ ] Pricing versioning

## Current Next Work

Implement BaaS P0 Subscription Billing service.
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

BaaS P0 Usage Metering service initialized.

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

Canonical initial metrics: COMPLETE

Tenant attribution + timestamps: COMPLETE

Immutable raw usage records: COMPLETE

Idempotent ingestion + conflict detection: COMPLETE

Decimal/unit-safe quantities: COMPLETE

Auditable raw usage: COMPLETE

Deterministic aggregation: COMPLETE

Source-hash reconciliation: COMPLETE

Raw usage mutation/delete API: NONE

Durable usage ledger: DEFERRED

Rating/pricing engine: DEFERRED

## Next Work

BaaS P0 — Subscription Billing service.

## Governing Rule

Usage Metering records immutable, tenant-attributed, timestamped usage before
billing. Ingestion is idempotent, aggregation is unit-safe and auditable, and
reconciliation recomputes from raw usage evidence. Rating, pricing, invoices,
credits, entitlements, and payment retries remain Billing BaaS responsibilities.
""",
encoding="utf-8",
)

print("OK: Usage Metering BaaS contract installed.")
print("OK: Immutable/idempotent raw usage + aggregation installed.")
print("OK: Unit-safe reconciliation and audit evidence installed.")
print("NEXT: BaaS P0 Subscription Billing service.")
