#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"
SAAS = ROOT / "saas"
DOCS = ROOT / "docs"

required = [
    SAAS / "STATUS.md",
    VALIDATION / "PUBLIC_MVP_CRITERIA.md",
    VALIDATION / "design-partners/README.md",
    VALIDATION / "metrics/METRICS.md",
    VALIDATION / "pilots/PILOT_PLAN.md",
    VALIDATION / "release-gates/README.md",
    VALIDATION / "onboarding/README.md",
    VALIDATION / "feedback/README.md",
    VALIDATION / "incidents/README.md",
    VALIDATION / "support/README.md",
    VALIDATION / "design-partners/DISCOVERY_CONTRACT.md",
    VALIDATION / "runtime.py",
    DOCS / "FINAL_PHASE_MAP.md",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Phase 7 prerequisite/artifact: {path}"
        )

saas_status = (
    SAAS / "STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "PHASE 6: COMPLETE",
    "Phase 7 — Product-Market Validation.",
]:
    if phrase not in saas_status:
        raise SystemExit(
            "ERROR: Phase 6 closure not confirmed: "
            + phrase
        )

phase_map = (
    DOCS / "FINAL_PHASE_MAP.md"
).read_text(
    encoding="utf-8"
)

if (
    "Phase 7 — Product-Market Validation"
    not in phase_map
):
    raise SystemExit(
        "ERROR: canonical Phase 7 map entry missing"
    )

py_compile.compile(
    str(
        VALIDATION / "runtime.py"
    ),
    doraise=True,
)

(VALIDATION / "README.md").write_text(
"""# Product-Market Validation

## Phase

Phase 7 — Product-Market Validation

## Purpose

Validate real merchant demand, activation, engagement, reliability, willingness
to pay, and operating support requirements before Platform Hardening and broader
product expansion.

Phase 7 records evidence. It must not fabricate interviews, merchants,
transactions, payments, retention, or product-market fit.

## Canonical Sequence

Discovery
→ Design Partners
→ Controlled Pilot
→ Repeatable Onboarding
→ Validation Metrics
→ Pilot Exit Gate
→ Public MVP Gate
→ Phase 7 Decision

## Discovery + Design Partners

Target:

- 20–30 discovery interviews
- 5–10 design partner commitments
- minimum 3 active pilot merchants
- at least 80% confirm the core problem is material

The runtime enforces canonical partner-selection evidence and computes the
Discovery + Design Partner gate from actual recorded evidence.

## Controlled Public MVP Capacity

- 100 organizations
- 250 POS branches
- 10,000 monthly orders

These are caps, not growth targets.

## Evidence Areas

- Design Partners
- Onboarding
- Pilots
- Metrics
- Feedback
- Support
- Incidents
- Release Gates

## Governing Rule

No Phase 7 business outcome becomes COMPLETE from code or documentation alone.
External merchant, transaction, reliability, commercial, and support outcomes
require recorded evidence.

## Current Work

Discovery + Design Partner evidence collection.

## Next Work

Pilot onboarding + validation metrics + release-gate evidence.
""",
encoding="utf-8",
)

(VALIDATION / "STATUS.md").write_text(
"""# Product-Market Validation Status

## Phase

Phase 7 — Product-Market Validation

## Prerequisite

Phase 6 Commerce + POS MVP: COMPLETE

## Current Stage

Discovery + Design Partner evidence system initialized.

## Discovery

Interview target 20–30: EVIDENCE COLLECTION PENDING

Problem-material confirmation >=80%: EVIDENCE COLLECTION PENDING

## Design Partners

Commitment target 5–10: EVIDENCE COLLECTION PENDING

Minimum 3 active pilot merchants: EVIDENCE COLLECTION PENDING

Canonical selection criteria enforcement: COMPLETE

Evidence immutability/idempotency: COMPLETE

Opaque merchant/evidence references: COMPLETE

Sensitive/direct-contact metadata rejection: COMPLETE

Discovery gate computation: COMPLETE

## Controlled Capacity

Organizations cap: 100

POS branches cap: 250

Monthly orders cap: 10,000

Capacity expansion: NOT AUTHORIZED

## Business Outcome

Product-market fit: NOT YET ESTABLISHED

Discovery gate: PENDING REAL EVIDENCE

## Next Work

Pilot onboarding + validation metrics + release-gate evidence.

## Governing Rule

Code may validate evidence structure and gate mathematics, but it may not mark
merchant interviews, commitments, transactions, retention, willingness to pay,
or product-market fit as achieved without real evidence.
""",
encoding="utf-8",
)

(VALIDATION / "IMPLEMENTATION_STATUS.md").write_text(
"""# Phase 7 Implementation Status

## Foundation

- [x] Phase 6 completion prerequisite
- [x] Canonical Public MVP targets loaded
- [x] Canonical design-partner targets loaded
- [x] Canonical pilot criteria loaded
- [x] Canonical validation metrics identified
- [x] Canonical release gates identified
- [x] Controlled launch-cap contract

## Discovery + Design Partners

- [x] DiscoveryInterview evidence contract
- [x] DesignPartnerCommitment evidence contract
- [x] Canonical partner-selection criteria enforcement
- [x] COMMERCE/POS product scope validation
- [x] Timezone-aware evidence timestamps
- [x] Opaque merchant references
- [x] Opaque evidence references
- [x] Sensitive/direct-contact metadata rejection
- [x] Interview evidence immutability/idempotency
- [x] Commitment evidence immutability/idempotency
- [x] Duplicate merchant commitment rejection
- [x] Pilot status lifecycle
- [x] Discovery gate computation
- [x] Evidence digest

## External Evidence — Not Fabricated

- [ ] 20+ discovery interviews recorded
- [ ] >=80% problem-material confirmation
- [ ] 5+ design partner commitments
- [ ] 3+ active pilot merchants

## Phase 7 Result

ACTIVE — DISCOVERY EVIDENCE COLLECTION

## Current Next Work

Pilot onboarding + validation metrics + release-gate evidence.
""",
encoding="utf-8",
)

print("OK: Phase 7 validation foundation installed.")
print("OK: Discovery + Design Partner evidence registry installed.")
print("OK: Canonical 80%/20/5/3 gate and controlled launch caps installed.")
print("STATUS: PHASE 7 DISCOVERY + DESIGN PARTNERS READY")
print("NEXT: Pilot onboarding + validation metrics + release-gate evidence.")
