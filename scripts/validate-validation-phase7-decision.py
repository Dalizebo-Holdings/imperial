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
    sys.path.insert(0, root_text)

required = [
    VALIDATION / "STATUS.md",
    VALIDATION / "IMPLEMENTATION_STATUS.md",
    VALIDATION / "PUBLIC_MVP_CRITERIA.md",
    VALIDATION / "evidence/INGESTION_CONTRACT.md",
    VALIDATION / "evidence/runtime.py",
    VALIDATION / "decision/PMF_DECISION_CONTRACT.md",
    VALIDATION / "decision/runtime.py",
    VALIDATION / "runtime.py",
    VALIDATION / "pilot_runtime.py",
    VALIDATION / "operations_runtime.py",
    SAAS / "STATUS.md",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Phase 7 decision file: {path}"
        )

for path in [
    VALIDATION / "evidence/runtime.py",
    VALIDATION / "decision/runtime.py",
]:
    py_compile.compile(
        str(path),
        doraise=True,
    )

try:
    evidence = importlib.import_module(
        "validation.evidence.runtime"
    )
    decision = importlib.import_module(
        "validation.decision.runtime"
    )
except Exception as exc:
    raise SystemExit(
        f"ERROR: unable to import Phase 7 decision modules: {exc}"
    ) from exc

public = (
    VALIDATION / "PUBLIC_MVP_CRITERIA.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "50 activated organizations",
    "30 monthly transacting organizations",
    "20 active for 3 consecutive months",
    "Monthly logo churn < 5%",
    "30% reach first transaction within 24 hours",
    "60% weekly active usage",
    "Payment reconciliation >= 99.5%",
    "Uptime >= 99.5%",
    "P95 core API latency < 500ms",
    "Checkout API < 1.5s excluding payment provider",
    "At least 10 paying customers",
    "At least 3 customer references",
    "No critical tenant isolation defect",
    "Successful backup restore test",
]:
    if phrase not in public:
        raise SystemExit(
            "ERROR: canonical Public MVP target missing: "
            + phrase
        )

engine = decision.PMFDecisionEngine()

# Exact threshold fixture should pass the Public MVP evaluator.
snapshot = decision.PublicMVP90DaySnapshot(
    snapshot_id="public-mvp-test-pass",
    period_start="2026-06-01T00:00:00+02:00",
    period_end="2026-09-01T00:00:00+02:00",
    activated_organizations=50,
    monthly_transacting_organizations=30,
    active_three_consecutive_months=20,
    logo_start_count=100,
    logo_churned_count=4,
    first_transaction_eligible_organizations=50,
    first_transaction_within_24h=15,
    weekly_usage_eligible_organizations=50,
    weekly_active_organizations=30,
    payment_reconciliation_total=200,
    payment_reconciliation_matches=199,
    uptime_total_minutes=100000,
    uptime_available_minutes=99500,
    p95_core_api_latency_ms=499,
    checkout_api_p95_ms=1499,
    paying_customers=10,
    customer_references=3,
    critical_tenant_isolation_defects=0,
    backup_restore_test_passed=True,
    evidence_refs=(
        "evidence://fixture/public-mvp",
    ),
)

public_gate = engine.public_mvp_gate(
    snapshot
)

if public_gate.state != "PASS":
    raise SystemExit(
        "ERROR: exact canonical Public MVP thresholds did not pass"
    )

# Strict inequalities must remain strict.
bad_churn = decision.PublicMVP90DaySnapshot(
    **{
        **snapshot.__dict__,
        "snapshot_id": "public-mvp-bad-churn",
        "logo_churned_count": 5,
    }
)

if engine.public_mvp_gate(
    bad_churn
).state != "PENDING":
    raise SystemExit(
        "ERROR: 5% logo churn incorrectly passed <5% requirement"
    )

bad_latency = decision.PublicMVP90DaySnapshot(
    **{
        **snapshot.__dict__,
        "snapshot_id": "public-mvp-bad-latency",
        "p95_core_api_latency_ms": 500,
    }
)

if engine.public_mvp_gate(
    bad_latency
).state != "PENDING":
    raise SystemExit(
        "ERROR: 500ms P95 incorrectly passed <500ms requirement"
    )

ledger = evidence.EvidenceLedger()

def make_envelope(
    *,
    envelope_id,
    evidence_ref,
    origin,
    digest,
):
    payload = {
        "evidence_digest": digest,
        "fixture_context": (
            origin == "TEST_FIXTURE"
        ),
    }
    return evidence.EvidenceEnvelope(
        envelope_id=envelope_id,
        evidence_type="GATE_PROOF",
        origin=origin,
        observed_at="2026-09-09T08:00:00+02:00",
        evidence_ref=evidence_ref,
        source_system_ref="source://validation/test-validator",
        payload=payload,
        content_sha256=evidence.payload_sha256(
            payload
        ),
    )

required_labels = {
    "discovery": "PASS",
    "pilot_exit": "PASS",
    "release_gate_1": "PASS",
    "release_gate_2": "PASS",
    "release_gate_3": "PASS",
    "operational_readiness": "EVIDENCE_AVAILABLE",
    "public_mvp_90d": "PASS",
}

# TEST_FIXTURE proof must never close Phase 7.
fixture_proofs = []
for index, (
    label,
    state,
) in enumerate(
    required_labels.items()
):
    digest = (
        public_gate.evidence_digest
        if label == "public_mvp_90d"
        else f"{index + 1:064x}"
    )
    ref = (
        f"evidence://test/closure/{label}"
    )

    ledger.ingest(
        make_envelope(
            envelope_id=f"fixture-{label}",
            evidence_ref=ref,
            origin="TEST_FIXTURE",
            digest=digest,
        )
    )

    fixture_proofs.append(
        decision.GateProof(
            label=label,
            state=state,
            evidence_digest=digest,
            evidence_ref=ref,
        )
    )

fixture_result = engine.phase7_decision(
    ledger=ledger,
    proofs=tuple(
        fixture_proofs
    ),
)

if fixture_result.state != "CONTINUE_VALIDATION":
    raise SystemExit(
        "ERROR: TEST_FIXTURE evidence closed Phase 7"
    )

if not ledger.verify_chain():
    raise SystemExit(
        "ERROR: evidence ledger chain verification failed"
    )

# A separate real-origin fixture ledger exercises decision mechanics.
# These are validator objects only; they are never persisted as business evidence.
real_ledger = evidence.EvidenceLedger()
real_proofs = []

for index, (
    label,
    state,
) in enumerate(
    required_labels.items()
):
    digest = (
        public_gate.evidence_digest
        if label == "public_mvp_90d"
        else f"{index + 100:064x}"
    )
    ref = (
        f"evidence://validator-real-shaped/closure/{label}"
    )

    envelope = make_envelope(
        envelope_id=f"real-shaped-{label}",
        evidence_ref=ref,
        origin=(
            "REAL_OPERATIONAL"
            if label != "discovery"
            else "REAL_MERCHANT"
        ),
        digest=digest,
    )

    real_ledger.ingest(
        envelope
    )

    real_proofs.append(
        decision.GateProof(
            label=label,
            state=state,
            evidence_digest=digest,
            evidence_ref=ref,
        )
    )

real_result = engine.phase7_decision(
    ledger=real_ledger,
    proofs=tuple(
        real_proofs
    ),
)

if real_result.state != "PHASE7_COMPLETE":
    raise SystemExit(
        "ERROR: complete bound non-fixture proof set did not satisfy decision mechanics"
    )

if (
    real_result.next_phase
    != "Phase 8 — Platform Hardening"
):
    raise SystemExit(
        "ERROR: successful closure did not authorize canonical Phase 8"
    )

# Digest mismatch must fail closed.
tampered = list(
    real_proofs
)
tampered[0] = decision.GateProof(
    label=tampered[0].label,
    state=tampered[0].state,
    evidence_digest="f" * 64,
    evidence_ref=tampered[0].evidence_ref,
)

if engine.phase7_decision(
    ledger=real_ledger,
    proofs=tuple(
        tampered
    ),
).state != "CONTINUE_VALIDATION":
    raise SystemExit(
        "ERROR: unbound/tampered gate digest closed Phase 7"
    )

# Changed envelope ID material must fail closed.
first = make_envelope(
    envelope_id="idempotent-envelope",
    evidence_ref="evidence://validator-real-shaped/idempotent",
    origin="REAL_OPERATIONAL",
    digest="a" * 64,
)
real_ledger.ingest(first)

changed_payload = {
    "evidence_digest": "b" * 64,
    "fixture_context": False,
}

try:
    real_ledger.ingest(
        evidence.EvidenceEnvelope(
            envelope_id="idempotent-envelope",
            evidence_type="GATE_PROOF",
            origin="REAL_OPERATIONAL",
            observed_at="2026-09-09T08:00:00+02:00",
            evidence_ref="evidence://validator-real-shaped/idempotent-changed",
            source_system_ref="source://validation/test-validator",
            payload=changed_payload,
            content_sha256=evidence.payload_sha256(
                changed_payload
            ),
        )
    )
except evidence.EvidenceIngestionError:
    pass
else:
    raise SystemExit(
        "ERROR: evidence envelope mutation was accepted"
    )

status = (
    VALIDATION / "STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "Evidence ingestion + PMF decision/closure gate initialized.",
    "PHASE 7: NOT COMPLETE — REAL EVIDENCE REQUIRED",
    "Product-market fit: NOT YET ESTABLISHED",
    "Collect/import real Phase 7 evidence and run the PMF closure gate.",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Phase 7 status overclaims closure or misses next work: "
            + phrase
        )

print("OK: Public MVP 90-day canonical thresholds loaded.")
print("OK: Strict churn/latency boundaries passed.")
print("OK: Append-only SHA-256 evidence ledger passed.")
print("OK: TEST_FIXTURE evidence cannot close Phase 7.")
print("OK: Gate proof → evidence digest binding passed.")
print("OK: Tampered/unbound proof fails closed.")
print("OK: Complete non-fixture proof mechanics authorize Phase 8.")
print("STATUS: PHASE 7 EVIDENCE INGESTION + PMF DECISION GATE READY")
print("STATUS: PHASE 7 NOT COMPLETE — REAL EVIDENCE REQUIRED")
