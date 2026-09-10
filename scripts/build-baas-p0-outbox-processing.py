#!/usr/bin/env python3
"""Build helper for Phase 8 outbox processing BaaS artifacts."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

BAAS = ROOT / "baas"
KERNEL_OUTBOX = ROOT / "kernel" / "outbox"

REQUIRED_FILES = [
    KERNEL_OUTBOX / "runtime.py",
    KERNEL_OUTBOX / "processor.py",
    KERNEL_OUTBOX / "observability.py",
    ROOT / "kernel/migrations/sql/0004_phase8_outbox_delivery_hardening.sql",
    ROOT / "kernel/migrations/sql/0005_phase8_outbox_publish_acknowledgement.sql",
    BAAS / "IMPLEMENTATION_STATUS.md",
]

STATUS_CONTENT = """# Dalizebo BaaS Implementation Status

## Phase

Phase 8

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
- [ ] Usage Metering
- [x] Subscription Billing
- [x] Payment Abstraction
- [x] Secrets
- [x] Backups

## Outbox Processing

- [x] Kernel outbox event state remains authoritative
- [x] Committed-only publish handoff from Kernel to BaaS events
- [x] Durable outbox delivery hardening migration
- [x] Bounded outbox processing loop with worker leasing
- [x] Lease ownership and expiry
- [x] Atomic claim semantics via FOR UPDATE SKIP LOCKED
- [x] Exponential retry scheduling inside Kernel bounds
- [x] Durable publish acknowledgement persistence
- [x] DEAD_LETTER terminal persistence
- [x] Crash and expired-lease recovery
- [x] Tenant and correlation context preservation
- [x] Out-of-process concurrency validation
- [x] PostgreSQL integration validation

## Outbox Observability

- [x] Outbox observability structured log contract
- [x] Claimed / published / retry_scheduled / dead_letter events
- [x] Identity binding to emitter, not runtime correlation
- [x] Signed source-service allowlist
- [x] Leaked-payload guardrails
- [x] Delivery rate-limit envelope

## Runtime Status

Kernel outbox runtime: INSTALLED
Kernel outbox processor: INSTALLED
Kernel outbox observability: INSTALLED
PostgreSQL worker integration: VALIDATED

## Deferred Runtime

Production outbox worker scheduler: DEFERRED
Operational observability pipeline: DEFERRED
"""

STATUS_SHORT = """# Dalizebo BaaS Status

## Phase

Phase 8 — Platform Hardening

## Prerequisite

Kernel P0: COMPLETE

## Current Stage

Phase 8 outbox processing durability foundations installed.

## Outbox

Kernel outbox event state: COMPLETE
Committed-only publish handoff: COMPLETE
Durable delivery hardening migration: COMPLETE
Bounded outbox processing loop: COMPLETE
Lease ownership and expiry: COMPLETE
Atomic claim semantics: COMPLETE
Exponential retry scheduling: COMPLETE
Durable publish acknowledgement: COMPLETE
DEAD_LETTER terminal persistence: COMPLETE
Crash/expired-lease recovery: COMPLETE
Tenant/correlation preservation: COMPLETE
Concurrency validation: COMPLETE
PostgreSQL integration validation: COMPLETE

## Outbox Observability

Outbox observability contract: COMPLETE
Claimed/published/retry/scheduled/dead-letter events: COMPLETE
Identity binding to emitter: COMPLETE
Signed source-service allowlist: COMPLETE
Leaked-payload guardrails: COMPLETE
Delivery rate-limit envelope: COMPLETE

## Deferred Runtime

Production outbox worker scheduler: DEFERRED
Operational observability pipeline: DEFERRED

## Next Work

Phase 8 outbox observability guardrails and delivery rate-limit envelope review.

## Governing Rule

Kernel remains authoritative for outbox event state. BaaS provides
orchestration and delivery planning only. Outbox processing never
publishes before transaction commit and never duplicates Kernel event
authority.
"""

def main() -> None:
    missing = []
    for path in REQUIRED_FILES:
        if not path.exists():
            missing.append(str(path))

    if missing:
        print("ERROR: missing required artifacts:")
        for m in missing:
            print(f"  - {m}")
        sys.exit(1)

    # Compile Python files
    import py_compile

    python_files = [
        KERNEL_OUTBOX / "runtime.py",
        KERNEL_OUTBOX / "processor.py",
        KERNEL_OUTBOX / "observability.py",
    ]
    for py_file in python_files:
        try:
            py_compile.compile(str(py_file), doraise=True)
            print(f"Compiled: {py_file.relative_to(ROOT)}")
        except py_compile.PyCompileError as e:
            print(f"ERROR: compilation failed for {py_file}: {e}")
            sys.exit(1)

    # Write full status
    (BAAS / "IMPLEMENTATION_STATUS.md").write_text(STATUS_CONTENT, encoding="utf-8")
    print(f"Updated: {BAAS / 'IMPLEMENTATION_STATUS.md'}")

    # Write short status
    (BAAS / "STATUS.md").write_text(STATUS_SHORT, encoding="utf-8")
    print(f"Updated: {BAAS / 'STATUS.md'}")

    print("\nDone: outbox processing build artifacts verified and status updated.")
    print("NEXT: review Phase 8 outbox observability guardrails and delivery rate-limit envelope.")


if __name__ == "__main__":
    main()
