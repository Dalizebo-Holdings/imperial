#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"
SAAS = ROOT / "saas"

required = [
    SAAS / "STATUS.md",
    VALIDATION / "README.md",
    VALIDATION / "STATUS.md",
    VALIDATION / "IMPLEMENTATION_STATUS.md",
    VALIDATION / "runtime.py",
    VALIDATION / "PUBLIC_MVP_CRITERIA.md",
    VALIDATION / "design-partners/README.md",
    VALIDATION / "onboarding/README.md",
    VALIDATION / "onboarding/PILOT_ONBOARDING_CONTRACT.md",
    VALIDATION / "metrics/METRICS.md",
    VALIDATION / "metrics/PILOT_METRICS_CONTRACT.md",
    VALIDATION / "pilots/PILOT_PLAN.md",
    VALIDATION / "release-gates/README.md",
    VALIDATION / "release-gates/GATE_EVIDENCE_CONTRACT.md",
    VALIDATION / "pilot_runtime.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Phase 7 pilot prerequisite/artifact: {path}"
        )

saas_status = (
    SAAS / "STATUS.md"
).read_text(
    encoding="utf-8"
)

if "PHASE 6: COMPLETE" not in saas_status:
    raise SystemExit(
        "ERROR: Phase 6 is not confirmed complete"
    )

validation_status = (
    VALIDATION / "STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "Discovery + Design Partner evidence system initialized.",
    "Pilot onboarding + validation metrics + release-gate evidence.",
]:
    if phrase not in validation_status:
        raise SystemExit(
            "ERROR: Phase 7 foundation not confirmed: "
            + phrase
        )

for path in [
    VALIDATION / "runtime.py",
    VALIDATION / "pilot_runtime.py",
]:
    py_compile.compile(
        str(path),
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

Evidence systems may validate structure, consistency, and gate mathematics.
They may not fabricate interviews, merchants, transactions, retention,
reliability, commercial outcomes, or product-market fit.

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

Control plane: COMPLETE

External evidence: PENDING REAL EVIDENCE

Gate:

- 20+ interviews
- >=80% core-problem confirmation
- 5+ commitments
- 3+ active pilot merchants

## Pilot Onboarding

Evidence control plane: COMPLETE

Canonical product-aware onboarding sequence: COMPLETE

24-hour first-sale measurement: COMPLETE

Import/payment failures, training and support interventions: TRACKED

Actual merchant onboarding outcomes: PENDING REAL EVIDENCE

## Pilot Metrics

Activation/engagement/reliability/commercial/support schema: COMPLETE

Pilot exit gate computation: COMPLETE

Actual KPI results: PENDING REAL EVIDENCE

## Release Gates

Gate 1 evaluator: COMPLETE

Gate 2 evaluator: COMPLETE

Gate 3 evaluator: COMPLETE

Technical/operational evidence attestations: COMPLETE

Expired evidence rejection: COMPLETE

Actual gate passage: PENDING REAL EVIDENCE

## Controlled Public MVP Capacity

- 100 organizations
- 250 POS branches
- 10,000 monthly orders

Capacity expansion: NOT AUTHORIZED

## Governing Rule

No Phase 7 business outcome becomes COMPLETE from code or documentation alone.

## Current Work

Controlled pilot evidence collection.

## Next Work

Feedback + Support + Incident evidence system.
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

Pilot onboarding + validation metrics + release-gate evidence system initialized.

## Discovery

Interview target 20–30: EVIDENCE COLLECTION PENDING

Problem-material confirmation >=80%: EVIDENCE COLLECTION PENDING

## Design Partners

Commitment target 5–10: EVIDENCE COLLECTION PENDING

Minimum 3 active pilot merchants: EVIDENCE COLLECTION PENDING

Discovery gate computation: COMPLETE

## Pilot Onboarding

Product-aware onboarding workflow: COMPLETE

24-hour first-sale calculation: COMPLETE

Failure/training/support tracking: COMPLETE

Actual merchants onboarded: EVIDENCE COLLECTION PENDING

## Pilot Metrics

Activation metrics: COMPLETE

Engagement metrics: COMPLETE

Reliability metrics: COMPLETE

Commercial metrics: COMPLETE

Support metrics: COMPLETE

Pilot exit gate: COMPLETE

Actual KPI thresholds: EVIDENCE COLLECTION PENDING

## Release Gates

Gate 1 evaluator: COMPLETE

Gate 2 evaluator: COMPLETE

Gate 3 evaluator: COMPLETE

Evidence expiry handling: COMPLETE

Actual Gate 1 passage: PENDING REAL EVIDENCE

Actual Gate 2 passage: PENDING REAL EVIDENCE

Actual Gate 3 passage: PENDING REAL EVIDENCE

## Controlled Capacity

Organizations cap: 100

POS branches cap: 250

Monthly orders cap: 10,000

Capacity gate: COMPLETE

Capacity expansion: NOT AUTHORIZED

## Business Outcome

Product-market fit: NOT YET ESTABLISHED

Phase 7: ACTIVE — CONTROLLED PILOT EVIDENCE COLLECTION

## Next Work

Feedback + Support + Incident evidence system.

## Governing Rule

External merchant, transaction, reliability, support, commercial, regulatory,
and release-gate outcomes require real evidence. Validator test fixtures never
count as business evidence.
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
- [x] Evidence immutability/idempotency
- [x] Discovery gate computation

## Pilot Onboarding

- [x] ACTIVE design-partner prerequisite
- [x] Product-aware onboarding workflow
- [x] Organization/Store setup evidence
- [x] POS Branch/Staff setup evidence
- [x] Product import evidence
- [x] Inventory setup evidence
- [x] Payment setup evidence
- [x] Test sale evidence
- [x] First live transaction evidence
- [x] Sequential success enforcement
- [x] Failed-attempt/retry support
- [x] 24-hour first-sale calculation
- [x] Import failure tracking
- [x] Payment setup failure tracking
- [x] Training/support intervention tracking
- [x] Evidence immutability/idempotency

## Pilot Metrics

- [x] Activation counters
- [x] Engagement counters
- [x] Reliability counters
- [x] Commercial counters
- [x] Support counters
- [x] Deterministic rate calculation
- [x] Numerator/denominator integrity
- [x] 7-day weekly measurement minimum
- [x] Canonical pilot exit gate
- [x] Controlled capacity gate

## Release Gates

- [x] Gate 1 Discovery→Alpha evaluator
- [x] Gate 2 Alpha→Pilot evaluator
- [x] Gate 3 Pilot→Public MVP evaluator
- [x] Technical/operational evidence attestations
- [x] Evidence expiry handling
- [x] Real transaction/reconciliation/onboarding linkage
- [x] Willingness-to-pay linkage
- [x] Tenant-isolation linkage
- [x] Controlled-capacity linkage

## External Evidence — Not Fabricated

- [ ] 20+ discovery interviews recorded
- [ ] >=80% problem-material confirmation
- [ ] 5+ design partner commitments
- [ ] 3+ active pilot merchants
- [ ] 5+ merchants fully onboarded
- [ ] >=70% weekly transacting
- [ ] >=80% first sale within 24 hours
- [ ] >=90% correct final order state
- [ ] >=99.5% payment reconciliation
- [ ] >=98% inventory accuracy
- [ ] 3+ merchants want to continue
- [ ] 2+ merchants willing to pay
- [ ] No critical cross-tenant exposure
- [ ] Release Gate 1 passed with evidence
- [ ] Release Gate 2 passed with evidence
- [ ] Release Gate 3 passed with evidence

## Phase 7 Result

ACTIVE — CONTROLLED PILOT EVIDENCE COLLECTION

## Current Next Work

Feedback + Support + Incident evidence system.
""",
encoding="utf-8",
)

print("OK: Phase 7 pilot onboarding control plane installed.")
print("OK: Pilot metrics + canonical exit gate installed.")
print("OK: Release Gates 1/2/3 evidence evaluators installed.")
print("OK: Controlled-capacity gate installed.")
print("STATUS: PHASE 7 PILOT ONBOARDING + METRICS + RELEASE GATES READY")
print("NEXT: Feedback + Support + Incident evidence system.")
