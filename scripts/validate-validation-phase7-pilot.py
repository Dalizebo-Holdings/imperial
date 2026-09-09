#!/usr/bin/env python3
from pathlib import Path
from datetime import timedelta
from types import SimpleNamespace
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
    VALIDATION / "runtime.py",
    VALIDATION / "pilot_runtime.py",
    VALIDATION / "onboarding/README.md",
    VALIDATION / "onboarding/PILOT_ONBOARDING_CONTRACT.md",
    VALIDATION / "metrics/METRICS.md",
    VALIDATION / "metrics/PILOT_METRICS_CONTRACT.md",
    VALIDATION / "pilots/PILOT_PLAN.md",
    VALIDATION / "release-gates/README.md",
    VALIDATION / "release-gates/GATE_EVIDENCE_CONTRACT.md",
    VALIDATION / "PUBLIC_MVP_CRITERIA.md",
    SAAS / "STATUS.md",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Phase 7 pilot file: {path}"
        )

for path in [
    VALIDATION / "runtime.py",
    VALIDATION / "pilot_runtime.py",
]:
    py_compile.compile(
        str(path),
        doraise=True,
    )

try:
    pilot = importlib.import_module(
        "validation.pilot_runtime"
    )
except Exception as exc:
    raise SystemExit(
        f"ERROR: unable to import validation.pilot_runtime: {exc}"
    ) from exc

onboarding_doc = (
    VALIDATION / "onboarding/README.md"
).read_text(
    encoding="utf-8"
)
for phrase in [
    "Organization Creation",
    "Store Setup",
    "Branch Setup",
    "Staff",
    "Product Import",
    "Inventory Setup",
    "Payment Setup",
    "Test Sale",
    "First Live Transaction",
    "First successful sale within 24 hours",
]:
    if phrase not in onboarding_doc:
        raise SystemExit(
            "ERROR: canonical onboarding requirement missing: "
            + phrase
        )

pilot_plan = (
    VALIDATION / "pilots/PILOT_PLAN.md"
).read_text(
    encoding="utf-8"
)
for phrase in [
    "At least 5 merchants onboarded",
    "At least 70% transact weekly",
    "At least 80% reach first sale within 24 hours",
    "At least 90% of orders reach correct final state",
    "Payment reconciliation >= 99.5%",
    "Inventory accuracy >= 98%",
    "At least 3 merchants want to continue",
    "At least 2 merchants are willing to pay",
    "No critical cross-tenant exposure",
]:
    if phrase not in pilot_plan:
        raise SystemExit(
            "ERROR: canonical pilot exit criterion missing: "
            + phrase
        )

release_doc = (
    VALIDATION / "release-gates/README.md"
).read_text(
    encoding="utf-8"
)
for phrase in [
    "Gate 1 — Discovery to Alpha",
    "Gate 2 — Alpha to Pilot",
    "Gate 3 — Pilot to Public MVP",
    "Tenant isolation tests",
    "Backup restore test",
    "At least 2 merchants willing to pay",
]:
    if phrase not in release_doc:
        raise SystemExit(
            "ERROR: canonical release-gate requirement missing: "
            + phrase
        )

registry = pilot.PilotValidationRegistry()

active_commitments = []
for index in range(5):
    active_commitments.append(
        SimpleNamespace(
            commitment_id=(
                f"commitment-test-{index}"
            ),
            merchant_ref=(
                f"merchant://pilot/{index}"
            ),
            products=(
                ("COMMERCE", "POS")
            ),
            pilot_status="ACTIVE",
        )
    )

# Inactive partners cannot start pilot onboarding.
try:
    registry.start_onboarding(
        commitment=SimpleNamespace(
            commitment_id="inactive",
            merchant_ref="merchant://inactive",
            products=("POS",),
            pilot_status="CANDIDATE",
        ),
        onboarding=pilot.PilotOnboarding(
            onboarding_id="onboarding-inactive",
            commitment_id="inactive",
            merchant_ref="merchant://inactive",
            products=("POS",),
            started_at="2026-09-01T08:00:00+02:00",
            evidence_ref="evidence://test/inactive",
            metadata={},
        ),
    )
except pilot.PilotValidationError:
    pass
else:
    raise SystemExit(
        "ERROR: inactive design partner started pilot onboarding"
    )

required_steps = (
    "ORGANIZATION_CREATION",
    "STORE_SETUP",
    "BRANCH_SETUP",
    "STAFF",
    "PRODUCT_IMPORT",
    "INVENTORY_SETUP",
    "PAYMENT_SETUP",
    "TEST_SALE",
    "FIRST_LIVE_TRANSACTION",
)

# Five completed pilot onboardings; four within 24h, one after 24h.
for index, commitment in enumerate(
    active_commitments
):
    onboarding = pilot.PilotOnboarding(
        onboarding_id=(
            f"onboarding-test-{index}"
        ),
        commitment_id=(
            commitment.commitment_id
        ),
        merchant_ref=(
            commitment.merchant_ref
        ),
        products=("COMMERCE", "POS"),
        started_at=(
            f"2026-09-0{index + 1}T08:00:00+02:00"
        ),
        evidence_ref=(
            f"evidence://test/onboarding/{index}"
        ),
        metadata={
            "fixture": True,
        },
    )

    started = registry.start_onboarding(
        commitment=commitment,
        onboarding=onboarding,
    )

    if started["created"] is not True:
        raise SystemExit(
            "ERROR: onboarding fixture was not created"
        )

    # Exact replay is idempotent.
    replay = registry.start_onboarding(
        commitment=commitment,
        onboarding=onboarding,
    )
    if replay["created"] is not False:
        raise SystemExit(
            "ERROR: onboarding idempotency failed"
        )

    day = index + 1

    for step_index, step in enumerate(
        required_steps
    ):
        hour_offset = step_index * 2

        if (
            step == "FIRST_LIVE_TRANSACTION"
            and index == 4
        ):
            occurred = (
                "2026-09-06T10:00:00+02:00"
            )
        else:
            hour = 8 + hour_offset
            event_day = day
            while hour >= 24:
                hour -= 24
                event_day += 1
            occurred = (
                f"2026-09-{event_day:02d}T{hour:02d}:00:00+02:00"
            )

        # Exercise a failed import retry for merchant 0.
        if (
            index == 0
            and step == "PRODUCT_IMPORT"
        ):
            failed = registry.record_onboarding_event(
                pilot.OnboardingEvent(
                    event_id="event-import-failed",
                    onboarding_id=(
                        onboarding.onboarding_id
                    ),
                    merchant_ref=(
                        onboarding.merchant_ref
                    ),
                    step=step,
                    status="FAILED",
                    occurred_at=occurred,
                    evidence_ref=(
                        "evidence://test/import-failed"
                    ),
                    failure_code="IMPORT_FORMAT",
                    training_required=True,
                    support_intervention=True,
                    metadata={
                        "fixture": True,
                    },
                )
            )
            if failed["created"] is not True:
                raise SystemExit(
                    "ERROR: failed import fixture missing"
                )

            # successful retry one hour later
            dt = pilot._time(
                occurred
            ) + timedelta(
                hours=1
            )
            occurred = dt.isoformat()

        registry.record_onboarding_event(
            pilot.OnboardingEvent(
                event_id=(
                    f"event-{index}-{step.lower()}"
                ),
                onboarding_id=(
                    onboarding.onboarding_id
                ),
                merchant_ref=(
                    onboarding.merchant_ref
                ),
                step=step,
                status="SUCCESS",
                occurred_at=occurred,
                evidence_ref=(
                    f"evidence://test/event/{index}/{step.lower()}"
                ),
                metadata={
                    "fixture": True,
                },
            )
        )

summary0 = registry.onboarding_summary(
    "onboarding-test-0"
)

if (
    not summary0.completed
    or summary0.import_failure_count != 1
    or summary0.training_requirement_count != 1
    or summary0.support_intervention_count != 1
):
    raise SystemExit(
        "ERROR: onboarding derived evidence mismatch"
    )

summaries = [
    registry.onboarding_summary(
        f"onboarding-test-{index}"
    )
    for index in range(5)
]

if sum(
    1
    for summary in summaries
    if summary.first_sale_within_24h
) != 4:
    raise SystemExit(
        "ERROR: 24-hour first-sale calculation mismatch"
    )

snapshot = pilot.PilotMetricSnapshot(
    snapshot_id="pilot-metrics-pass",
    period_start="2026-09-01T00:00:00+02:00",
    period_end="2026-09-08T00:00:00+02:00",
    evidence_ref="evidence://test/metrics/pass",
    weekly_active_merchants=4,
    orders_total=100,
    orders_correct_final_state=90,
    pos_transactions=60,
    commerce_transactions=40,
    active_branches=10,
    active_pos_locations=3,
    checkout_attempts=100,
    successful_checkouts=98,
    payment_reconciliation_total=200,
    payment_reconciliation_matches=199,
    inventory_checks=100,
    inventory_accurate_checks=98,
    api_requests=1000,
    api_errors=2,
    paying_merchants=2,
    trial_merchants=5,
    trial_to_paid_merchants=2,
    mrr_minor=100000,
    logo_start_count=5,
    logo_churned_count=0,
    merchants_willing_to_continue=3,
    merchants_willing_to_pay=2,
    support_tickets=4,
    engineering_interventions=1,
    critical_cross_tenant_defects=0,
    metadata={
        "fixture": True,
    },
)

registry.record_metric_snapshot(
    snapshot
)

pilot_exit = registry.pilot_exit_gate(
    "pilot-metrics-pass"
)

if pilot_exit.state != "PASS":
    raise SystemExit(
        "ERROR: exact canonical pilot exit thresholds did not pass"
    )

if (
    abs(
        pilot_exit.rates[
            "payment_reconciliation_rate"
        ]
        - 0.995
    )
    > 1e-12
):
    raise SystemExit(
        "ERROR: payment reconciliation rate calculation failed"
    )

capacity = pilot.CapacitySnapshot(
    snapshot_id="capacity-pass",
    observed_at="2026-09-08T12:00:00+02:00",
    organizations=100,
    pos_branches=250,
    monthly_orders=10000,
    evidence_ref="evidence://test/capacity/pass",
)

registry.record_capacity_snapshot(
    capacity
)

if (
    registry.capacity_gate(
        "capacity-pass"
    ).state
    != "PASS"
):
    raise SystemExit(
        "ERROR: exact controlled capacity should pass"
    )

registry.record_capacity_snapshot(
    pilot.CapacitySnapshot(
        snapshot_id="capacity-violation",
        observed_at="2026-09-08T12:01:00+02:00",
        organizations=101,
        pos_branches=250,
        monthly_orders=10000,
        evidence_ref="evidence://test/capacity/violation",
    )
)

if (
    registry.capacity_gate(
        "capacity-violation"
    ).state
    != "VIOLATION"
):
    raise SystemExit(
        "ERROR: controlled capacity expansion was not blocked"
    )

# Release gates are pending before explicit technical evidence.
discovery_gate = SimpleNamespace(
    state="PASS",
    material_problem_rate=0.80,
    commitment_count=5,
)

if (
    registry.release_gate_1(
        discovery_gate=discovery_gate,
        evaluated_at="2026-09-08T13:00:00+02:00",
    ).state
    != "PENDING"
):
    raise SystemExit(
        "ERROR: Gate 1 passed without technical evidence"
    )

# Install valid attestations for all three canonical gates.
for index, requirement in enumerate(
    sorted(
        pilot.ALL_ATTESTATIONS
    )
):
    registry.record_attestation(
        pilot.TechnicalAttestation(
            attestation_id=(
                f"attestation-{index}"
            ),
            requirement=requirement,
            satisfied=True,
            observed_at=(
                "2026-09-08T12:00:00+02:00"
            ),
            evidence_ref=(
                f"evidence://test/attestation/{index}"
            ),
            valid_until=(
                "2026-10-08T12:00:00+02:00"
            ),
            metadata={
                "fixture": True,
            },
        )
    )

if (
    registry.release_gate_1(
        discovery_gate=discovery_gate,
        evaluated_at="2026-09-09T12:00:00+02:00",
    ).state
    != "PASS"
):
    raise SystemExit(
        "ERROR: Gate 1 evidence evaluation failed"
    )

if (
    registry.release_gate_2(
        evaluated_at="2026-09-09T12:00:00+02:00",
    ).state
    != "PASS"
):
    raise SystemExit(
        "ERROR: Gate 2 evidence evaluation failed"
    )

if (
    registry.release_gate_3(
        snapshot_id="pilot-metrics-pass",
        capacity_snapshot_id="capacity-pass",
        evaluated_at="2026-09-09T12:00:00+02:00",
    ).state
    != "PASS"
):
    raise SystemExit(
        "ERROR: Gate 3 evidence evaluation failed"
    )

# Expired evidence cannot pass a gate.
registry.record_attestation(
    pilot.TechnicalAttestation(
        attestation_id="attestation-support-new-expired",
        requirement="SUPPORT_PROCESS",
        satisfied=True,
        observed_at="2026-10-09T12:00:00+02:00",
        evidence_ref="evidence://test/support/expired",
        valid_until="2026-10-10T12:00:00+02:00",
        metadata={},
    )
)

if (
    registry.release_gate_3(
        snapshot_id="pilot-metrics-pass",
        capacity_snapshot_id="capacity-pass",
        evaluated_at="2026-10-11T12:00:00+02:00",
    ).state
    != "PENDING"
):
    raise SystemExit(
        "ERROR: expired release-gate evidence remained valid"
    )

# Sensitive metadata must fail.
try:
    registry.record_metric_snapshot(
        pilot.PilotMetricSnapshot(
            **{
                **snapshot.__dict__,
                "snapshot_id": "sensitive-metrics",
                "metadata": {
                    "email": "not-allowed@example.com",
                },
            }
        )
    )
except pilot.PilotValidationError:
    pass
else:
    raise SystemExit(
        "ERROR: sensitive metric metadata was accepted"
    )

status = (
    VALIDATION / "IMPLEMENTATION_STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "ACTIVE — CONTROLLED PILOT EVIDENCE COLLECTION",
    "- [ ] 5+ merchants fully onboarded",
    "- [ ] >=70% weekly transacting",
    "- [ ] >=99.5% payment reconciliation",
    "- [ ] 2+ merchants willing to pay",
    "- [ ] Release Gate 3 passed with evidence",
    "run the PMF closure gate; Phase 8 remains blocked",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Phase 7 pilot status claims external evidence or misses next work: "
            + phrase
        )

print("OK: ACTIVE design-partner onboarding prerequisite passed.")
print("OK: Product-aware sequential onboarding/retry evidence passed.")
print("OK: 24-hour first-sale calculation passed.")
print("OK: Canonical pilot KPI calculations passed.")
print("OK: Exact pilot exit thresholds passed with fixtures.")
print("OK: Controlled capacity 100/250/10,000 enforced.")
print("OK: Gate 1/2/3 require explicit non-expired evidence.")
print("OK: Sensitive/direct-contact metadata is rejected.")
print("STATUS: PHASE 7 PILOT ONBOARDING + METRICS + RELEASE GATES READY")
