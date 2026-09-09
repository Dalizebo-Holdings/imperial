#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
SAAS = ROOT / "saas"

required = [
    SAAS / "STATUS.md",
    SAAS / "IMPLEMENTATION_STATUS.md",
    SAAS / "MVP_ACCEPTANCE.md",
    SAAS / "PHASE6_MVP_ACCEPTANCE.md",
    SAAS / "commerce/refunds/REFUNDS_CONTRACT.md",
    SAAS / "commerce/refunds/runtime.py",
    ROOT / "scripts/validate-saas-phase6-mvp.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Phase 6 closure artifact/prerequisite: {path}"
        )

# Prove acceptance before changing completion status.
proof = subprocess.run(
    [
        sys.executable,
        str(ROOT / "scripts/validate-saas-phase6-mvp.py"),
    ],
    cwd=ROOT,
    text=True,
    capture_output=True,
)

if proof.returncode != 0:
    if proof.stdout:
        print(proof.stdout, end="")
    if proof.stderr:
        print(proof.stderr, end="", file=sys.stderr)
    raise SystemExit(
        "ERROR: Phase 6 MVP acceptance failed; status was not advanced"
    )

status_path = SAAS / "STATUS.md"
status = status_path.read_text(
    encoding="utf-8"
)

if "PHASE 6: COMPLETE" not in status:
    old = """## Phase 6

Commerce P0: COMPLETE

POS P0: COMPLETE

MVP acceptance/integration closure: NEXT

## Next Work

Phase 6 — Commerce + POS MVP Acceptance & Integration Closure.
"""

    new = """## Phase 6

Commerce P0: COMPLETE

POS P0: COMPLETE

MVP acceptance/integration closure: COMPLETE

PHASE 6: COMPLETE

## Commerce Refund Closure

Auditable provider refund orchestration: COMPLETE

Kernel Refund cumulative cap: COMPLETE

BaaS Payment Abstraction refund delegation: COMPLETE

Partial refund preserves CAPTURED Payment: COMPLETE

Full cumulative refund CAPTURED→REFUNDED: COMPLETE

## MVP Acceptance

Commerce criteria: PASS

POS criteria: PASS

Platform criteria: PASS

## Next Work

Phase 7 — Product-Market Validation.
"""

    if old not in status:
        raise SystemExit(
            "ERROR: expected pre-closure Phase 6 status block not found"
        )

    status = status.replace(
        "## Current Stage\n\nDalizebo POS P0 complete.",
        "## Current Stage\n\nPhase 6 Commerce + POS MVP complete.",
    )
    status = status.replace(
        old,
        new,
    )

    status = status.replace(
        "## Governing Rule\n\n",
        "## Governing Rule\n\n"
        "Phase 6 completion is an MVP/P0 implementation milestone, not a "
        "declaration of full production hardening. "
    )

    status_path.write_text(
        status,
        encoding="utf-8",
    )

impl_path = SAAS / "IMPLEMENTATION_STATUS.md"
impl = impl_path.read_text(
    encoding="utf-8"
)

if "PHASE 6: COMPLETE" not in impl:
    old_impl = """## Phase 6 State

Commerce P0: COMPLETE

POS P0: COMPLETE

MVP acceptance/integration sweep: NEXT

## Current Next Work

Phase 6 — Commerce + POS MVP Acceptance & Integration Closure.
"""

    new_impl = """## Commerce Refund Closure

- [x] Provider refund planning through BaaS Payment Abstraction
- [x] Shared Kernel Refund validation
- [x] Auditable shared REFUND command
- [x] Partial refund preserves CAPTURED Payment
- [x] Full cumulative refund explicitly transitions CAPTURED→REFUNDED
- [x] Cross-tenant refund evidence rejection
- [x] Refund idempotency

## Phase 6 MVP Acceptance

- [x] Commerce acceptance criteria
- [x] POS acceptance criteria
- [x] No cross-tenant exposure gate
- [x] No duplicated authoritative SaaS SQL models
- [x] Critical-operation idempotency
- [x] Audit evidence
- [x] Payment reconciliation
- [x] Logging + metrics platform evidence
- [x] Backup restore-test platform evidence

## Phase 6 State

Commerce P0: COMPLETE

POS P0: COMPLETE

MVP acceptance/integration sweep: COMPLETE

PHASE 6: COMPLETE

## Current Next Work

Phase 7 — Product-Market Validation.
"""

    if old_impl not in impl:
        raise SystemExit(
            "ERROR: expected pre-closure implementation status block not found"
        )

    impl = impl.replace(
        old_impl,
        new_impl,
    )

    impl_path.write_text(
        impl,
        encoding="utf-8",
    )

print(proof.stdout, end="")
print("STATUS: PHASE 6 COMMERCE + POS MVP COMPLETE")
print("NEXT: Phase 7 — Product-Market Validation.")
