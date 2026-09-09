#!/usr/bin/env python3
from pathlib import Path
import importlib
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"
SAAS = ROOT / "saas"

root_text = str(ROOT)
if root_text not in sys.path:
    sys.path.insert(
        0,
        root_text,
    )

required = [
    VALIDATION / "README.md",
    VALIDATION / "STATUS.md",
    VALIDATION / "IMPLEMENTATION_STATUS.md",
    VALIDATION / "PUBLIC_MVP_CRITERIA.md",
    VALIDATION / "design-partners/README.md",
    VALIDATION / "design-partners/DISCOVERY_CONTRACT.md",
    VALIDATION / "runtime.py",
    VALIDATION / "pilots/PILOT_PLAN.md",
    VALIDATION / "metrics/METRICS.md",
    VALIDATION / "release-gates/README.md",
    SAAS / "STATUS.md",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Phase 7 validation file: {path}"
        )

py_compile.compile(
    str(
        VALIDATION / "runtime.py"
    ),
    doraise=True,
)

try:
    runtime = importlib.import_module(
        "validation.runtime"
    )
except Exception as exc:
    raise SystemExit(
        f"ERROR: unable to import validation.runtime: {exc}"
    ) from exc

design_doc = (
    VALIDATION / "design-partners/README.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "20–30 discovery interviews",
    "5–10 design partner commitments",
    "Minimum 3 active pilot merchants",
    "At least 80% of interviewed merchants should confirm the core problem is material.",
]:
    if phrase not in design_doc:
        raise SystemExit(
            "ERROR: canonical design-partner target missing: "
            + phrase
        )

public = (
    VALIDATION / "PUBLIC_MVP_CRITERIA.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "100 organizations",
    "250 POS branches",
    "10,000 monthly orders",
    "Payment reconciliation >= 99.5%",
    "No critical tenant isolation defect",
    "Successful backup restore test",
]:
    if phrase not in public:
        raise SystemExit(
            "ERROR: canonical Public MVP criterion missing: "
            + phrase
        )

pilot = (
    VALIDATION / "pilots/PILOT_PLAN.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "At least 5 merchants onboarded",
    "At least 70% transact weekly",
    "At least 80% reach first sale within 24 hours",
    "Inventory accuracy >= 98%",
    "At least 2 merchants are willing to pay",
]:
    if phrase not in pilot:
        raise SystemExit(
            "ERROR: canonical pilot exit criterion missing: "
            + phrase
        )

registry = (
    runtime.ProductMarketValidationRegistry()
)

# Empty registry must never claim market validation.
empty_gate = registry.discovery_gate()

if (
    empty_gate.state != "PENDING"
    or empty_gate.interview_count != 0
    or empty_gate.material_problem_rate != 0.0
):
    raise SystemExit(
        "ERROR: empty evidence incorrectly passes discovery gate"
    )

if registry.launch_cap != {
    "organizations": 100,
    "pos_branches": 250,
    "monthly_orders": 10000,
}:
    raise SystemExit(
        "ERROR: controlled Public MVP launch cap mismatch"
    )

# Record 20 real-shaped evidence objects in the validator.
# These are synthetic test fixtures only and are not persisted as business evidence.
for index in range(20):
    result = registry.record_interview(
        runtime.DiscoveryInterview(
            interview_id=(
                f"test-interview-{index:02d}"
            ),
            merchant_ref=(
                f"merchant://test/{index:02d}"
            ),
            merchant_segment="TEST_FIXTURE",
            conducted_at=(
                f"2026-09-{(index % 9) + 1:02d}T10:00:00+02:00"
            ),
            products=(
                ("COMMERCE", "POS")
                if index % 2 == 0
                else ("POS",)
            ),
            core_problem_material=(
                index < 16
            ),
            willingness_to_test=True,
            structured_feedback_available=True,
            evidence_ref=(
                f"evidence://test/interview/{index:02d}"
            ),
            metadata={
                "fixture": True,
            },
        )
    )

    if result["created"] is not True:
        raise SystemExit(
            "ERROR: new interview was not created"
        )

# Exact duplicate is idempotent.
duplicate = registry.record_interview(
    runtime.DiscoveryInterview(
        interview_id="test-interview-00",
        merchant_ref="merchant://test/00",
        merchant_segment="TEST_FIXTURE",
        conducted_at="2026-09-01T10:00:00+02:00",
        products=("COMMERCE", "POS"),
        core_problem_material=True,
        willingness_to_test=True,
        structured_feedback_available=True,
        evidence_ref="evidence://test/interview/00",
        metadata={
            "fixture": True,
        },
    )
)

if duplicate["created"] is not False:
    raise SystemExit(
        "ERROR: duplicate interview idempotency failed"
    )

# 5 valid commitments, 3 active pilots.
for index in range(5):
    result = registry.record_commitment(
        runtime.DesignPartnerCommitment(
            commitment_id=(
                f"test-commitment-{index:02d}"
            ),
            merchant_ref=(
                f"merchant://partner/{index:02d}"
            ),
            products=("COMMERCE", "POS"),
            committed_at=(
                f"2026-09-{index + 1:02d}T12:00:00+02:00"
            ),
            active_retail_operations=True,
            real_inventory=True,
            real_customers=True,
            transaction_volume_confirmed=True,
            willingness_to_test=True,
            structured_feedback_available=True,
            pilot_status=(
                "ACTIVE"
                if index < 3
                else "CANDIDATE"
            ),
            evidence_ref=(
                f"evidence://test/commitment/{index:02d}"
            ),
            metadata={
                "fixture": True,
            },
        )
    )

    if result["created"] is not True:
        raise SystemExit(
            "ERROR: valid design partner was not created"
        )

gate = registry.discovery_gate()

if gate.state != "PASS":
    raise SystemExit(
        "ERROR: canonical 20/80%/5/3 discovery gate did not pass"
    )

if (
    gate.interview_count != 20
    or gate.material_problem_count != 16
    or abs(
        gate.material_problem_rate
        - 0.80
    ) > 1e-12
    or gate.commitment_count != 5
    or gate.active_pilot_count != 3
):
    raise SystemExit(
        "ERROR: discovery gate metric calculation mismatch"
    )

# 79% equivalent must fail.
low_rate = (
    runtime.ProductMarketValidationRegistry()
)

for index in range(20):
    low_rate.record_interview(
        runtime.DiscoveryInterview(
            interview_id=f"low-{index}",
            merchant_ref=f"merchant://low/{index}",
            merchant_segment="TEST_FIXTURE",
            conducted_at="2026-09-09T10:00:00+02:00",
            products=("POS",),
            core_problem_material=(
                index < 15
            ),
            willingness_to_test=True,
            structured_feedback_available=True,
            evidence_ref=f"evidence://low/{index}",
            metadata={},
        )
    )

for index in range(5):
    low_rate.record_commitment(
        runtime.DesignPartnerCommitment(
            commitment_id=f"low-c-{index}",
            merchant_ref=f"merchant://low-partner/{index}",
            products=("POS",),
            committed_at="2026-09-09T11:00:00+02:00",
            active_retail_operations=True,
            real_inventory=True,
            real_customers=True,
            transaction_volume_confirmed=True,
            willingness_to_test=True,
            structured_feedback_available=True,
            pilot_status=(
                "ACTIVE"
                if index < 3
                else "CANDIDATE"
            ),
            evidence_ref=f"evidence://low-c/{index}",
            metadata={},
        )
    )

if low_rate.discovery_gate().state != "PENDING":
    raise SystemExit(
        "ERROR: sub-80% problem confirmation incorrectly passed"
    )

# Invalid partner selection must fail closed.
try:
    registry.record_commitment(
        runtime.DesignPartnerCommitment(
            commitment_id="invalid-selection",
            merchant_ref="merchant://invalid/selection",
            products=("POS",),
            committed_at="2026-09-09T12:00:00+02:00",
            active_retail_operations=True,
            real_inventory=False,
            real_customers=True,
            transaction_volume_confirmed=True,
            willingness_to_test=True,
            structured_feedback_available=True,
            pilot_status="CANDIDATE",
            evidence_ref="evidence://invalid/selection",
            metadata={},
        )
    )
except runtime.ValidationEvidenceError:
    pass
else:
    raise SystemExit(
        "ERROR: invalid design partner selection was accepted"
    )

# Sensitive/direct-contact metadata must fail closed.
try:
    registry.record_interview(
        runtime.DiscoveryInterview(
            interview_id="sensitive-fixture",
            merchant_ref="merchant://sensitive",
            merchant_segment="TEST_FIXTURE",
            conducted_at="2026-09-09T13:00:00+02:00",
            products=("COMMERCE",),
            core_problem_material=True,
            willingness_to_test=True,
            structured_feedback_available=True,
            evidence_ref="evidence://sensitive",
            metadata={
                "email": "must-not-be-stored@example.com",
            },
        )
    )
except runtime.ValidationEvidenceError:
    pass
else:
    raise SystemExit(
        "ERROR: direct-contact metadata was accepted"
    )

# Timezone-naive evidence must fail.
try:
    registry.record_interview(
        runtime.DiscoveryInterview(
            interview_id="naive-time",
            merchant_ref="merchant://naive-time",
            merchant_segment="TEST_FIXTURE",
            conducted_at="2026-09-09T13:00:00",
            products=("POS",),
            core_problem_material=True,
            willingness_to_test=True,
            structured_feedback_available=True,
            evidence_ref="evidence://naive-time",
            metadata={},
        )
    )
except runtime.ValidationEvidenceError:
    pass
else:
    raise SystemExit(
        "ERROR: timezone-naive discovery evidence was accepted"
    )

status = (
    VALIDATION / "IMPLEMENTATION_STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "ACTIVE — DISCOVERY EVIDENCE COLLECTION",
    "- [ ] 20+ discovery interviews recorded",
    "- [ ] >=80% problem-material confirmation",
    "- [ ] 5+ design partner commitments",
    "- [ ] 3+ active pilot merchants",
    "Pilot onboarding + validation metrics + release-gate evidence.",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Phase 7 status incorrectly claims external results or misses next work: "
            + phrase
        )

print("OK: Canonical Phase 7 discovery/design-partner targets loaded.")
print("OK: Empty evidence cannot claim validation.")
print("OK: 20 interviews + 80% confirmation gate math passed.")
print("OK: 5 commitments + 3 active pilots gate math passed.")
print("OK: Invalid partner selection fails closed.")
print("OK: Evidence IDs are immutable/idempotent.")
print("OK: Sensitive/direct-contact metadata is rejected.")
print("OK: Timezone-aware evidence timestamps are enforced.")
print("OK: Public MVP launch caps remain 100/250/10,000.")
print("STATUS: PHASE 7 DISCOVERY + DESIGN PARTNERS READY")
