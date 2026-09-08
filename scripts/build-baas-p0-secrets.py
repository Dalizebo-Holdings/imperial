#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"
KERNEL = ROOT / "kernel"

required = [
    BAAS / "README.md",
    BAAS / "SERVICE_CONTRACT.md",
    BAAS / "secrets/README.md",
    BAAS / "secrets/SECRETS_CONTRACT.md",
    BAAS / "secrets/runtime.py",
    BAAS / "runtime/request_context.py",
    KERNEL / "secrets/README.md",
    KERNEL / "secrets/runtime.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Secrets prerequisite/artifact: {path}"
        )

for path in [
    BAAS / "secrets/runtime.py",
    BAAS / "runtime/request_context.py",
    KERNEL / "secrets/runtime.py",
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
- [ ] Backups

## Secrets P0 Components

- [x] Kernel Secret Reference authority boundary
- [x] Tenant/workspace/project/environment secret scope
- [x] Provider-neutral secret-manager registry
- [x] Encryption-at-rest provider requirement
- [x] Opaque secret references only
- [x] Explicit consumer allowlists
- [x] Kernel-backed reference registration
- [x] Reference-only access planning
- [x] Access audit evidence
- [x] Secret disablement
- [x] Rotation due calculation
- [x] Rotation planning
- [x] Rotation confirmation with old-reference disablement
- [x] Secret-bearing metadata rejection
- [x] Kernel authorization evidence requirement
- [x] No secret-value field/API

## Secrets Deferred Runtime

- [ ] Production Vault/KMS/cloud secret-manager adapter
- [ ] Physical encryption-at-rest implementation
- [ ] Secret generation
- [ ] Runtime secret value retrieval/injection
- [ ] Automatic rotation execution
- [ ] Rotation scheduler

## Current Next Work

Implement BaaS P0 Backups service.
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

BaaS P0 Secrets service initialized.

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

## Secrets

Secrets BaaS: COMPLETE

Kernel Secret Reference boundary: COMPLETE

Full BaaS tenant/environment scope: COMPLETE

Provider-neutral secret-manager policy: COMPLETE

Opaque reference registration: COMPLETE

Consumer allowlists: COMPLETE

Reference-only access planning: COMPLETE

Access audit evidence: COMPLETE

Disablement: COMPLETE

Rotation due/planning/confirmation: COMPLETE

Secret-value field/API: NONE

Production secret-manager adapter: DEFERRED

Physical encryption/retrieval/injection: DEFERRED

Automatic rotation execution: DEFERRED

## Next Work

BaaS P0 — Backups service.

## Governing Rule

BaaS Secrets extends the Kernel Secret Reference Boundary without becoming a
vault. Raw secret values never enter BaaS control-plane state. Access resolves
only opaque references, consumer allowlists fail closed, rotation is explicit
and adapter-driven, and physical encryption/retrieval belongs to approved
production secret-manager adapters.
""",
encoding="utf-8",
)

print("OK: Secrets BaaS contract installed.")
print("OK: Kernel-backed registration + reference-only access installed.")
print("OK: Disablement + rotation planning/confirmation + audit evidence installed.")
print("NEXT: BaaS P0 Backups service.")
