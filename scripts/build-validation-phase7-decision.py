#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"
SAAS = ROOT / "saas"

required = [
    SAAS / "STATUS.md",
    VALIDATION / "STATUS.md",
    VALIDATION / "IMPLEMENTATION_STATUS.md",
    VALIDATION / "PUBLIC_MVP_CRITERIA.md",
    VALIDATION / "runtime.py",
    VALIDATION / "pilot_runtime.py",
    VALIDATION / "operations_runtime.py",
    VALIDATION / "evidence/INGESTION_CONTRACT.md",
    VALIDATION / "evidence/runtime.py",
    VALIDATION / "decision/PMF_DECISION_CONTRACT.md",
    VALIDATION / "decision/runtime.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Phase 7 decision prerequisite/artifact: {path}"
        )

if "PHASE 6: COMPLETE" not in (
    SAAS / "STATUS.md"
).read_text(
    encoding="utf-8"
):
    raise SystemExit(
        "ERROR: Phase 6 completion prerequisite missing"
    )

status_path = VALIDATION / "STATUS.md"
status = status_path.read_text(
    encoding="utf-8"
)

for phrase in [
    "Feedback + Support + Incident evidence system initialized.",
    "Phase 7 evidence ingestion + PMF decision/closure gate.",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: prior Phase 7 operational slice not confirmed: "
            + phrase
        )

for path in [
    VALIDATION / "runtime.py",
    VALIDATION / "pilot_runtime.py",
    VALIDATION / "operations_runtime.py",
    VALIDATION / "evidence/runtime.py",
    VALIDATION / "decision/runtime.py",
]:
    py_compile.compile(
        str(path),
        doraise=True,
    )

new_status = status.replace(
    "## Current Stage\n\nFeedback + Support + Incident evidence system initialized.",
    "## Current Stage\n\nEvidence ingestion + PMF decision/closure gate initialized.",
)

new_status = new_status.replace(
    "## Next Work\n\nPhase 7 evidence ingestion + PMF decision/closure gate.",
    """## Evidence Ingestion

Append-only evidence ledger: COMPLETE

Canonical payload SHA-256 verification: COMPLETE

Evidence chain digest: COMPLETE

Fixture-vs-real provenance separation: COMPLETE

Fixture evidence excluded from PMF decisions: COMPLETE

Gate-result evidence binding: COMPLETE

Independent third-party provenance verification: NOT CLAIMED

## Public MVP 90-Day Gate

50 activated organizations evaluator: COMPLETE

30 monthly transacting organizations evaluator: COMPLETE

20 active for 3 consecutive months evaluator: COMPLETE

Monthly logo churn <5% evaluator: COMPLETE

First transaction <=24h >=30% evaluator: COMPLETE

Weekly active usage >=60% evaluator: COMPLETE

Payment reconciliation >=99.5% evaluator: COMPLETE

Uptime >=99.5% evaluator: COMPLETE

P95 core API <500ms evaluator: COMPLETE

Checkout API <1.5s evaluator: COMPLETE

10+ paying customers evaluator: COMPLETE

3+ customer references evaluator: COMPLETE

Critical tenant-isolation blocker: COMPLETE

Backup restore-test requirement: COMPLETE

## PMF Decision / Closure Gate

Discovery proof binding: COMPLETE

Pilot Exit proof binding: COMPLETE

Release Gate 1/2/3 proof binding: COMPLETE

Operational readiness proof binding: COMPLETE

Public MVP 90-day proof binding: COMPLETE

Phase 8 authorization on complete real evidence: COMPLETE

## Phase 7 Closure State

PHASE 7: NOT COMPLETE — REAL EVIDENCE REQUIRED

Product-market fit: NOT YET ESTABLISHED

## Next Work

Collect/import real Phase 7 evidence and run the PMF closure gate. Phase 8 remains blocked until `PHASE7_COMPLETE`.""",
)

status_path.write_text(
    new_status,
    encoding="utf-8",
)

impl_path = VALIDATION / "IMPLEMENTATION_STATUS.md"
impl = impl_path.read_text(
    encoding="utf-8"
)

if "## Evidence Ingestion + PMF Decision" not in impl:
    marker = "## External Operational Evidence — Not Fabricated\n"
    insert = """## Evidence Ingestion + PMF Decision

- [x] Append-only evidence envelope ledger
- [x] Canonical payload SHA-256 verification
- [x] Evidence chain digest verification
- [x] REAL vs TEST_FIXTURE origin separation
- [x] Fixture evidence excluded from decisions
- [x] Gate proof → evidence digest binding
- [x] Public MVP 90-day evaluator
- [x] 50 activated organizations threshold
- [x] 30 monthly transacting organizations threshold
- [x] 20 active for three consecutive months threshold
- [x] Monthly logo churn <5%
- [x] First transaction <=24h >=30%
- [x] Weekly active usage >=60%
- [x] Payment reconciliation >=99.5%
- [x] Uptime >=99.5%
- [x] P95 core API latency <500ms
- [x] Checkout API P95 <1.5s
- [x] 10+ paying customers
- [x] 3+ customer references
- [x] Tenant-isolation blocker
- [x] Backup restore-test gate
- [x] Phase 7 closure proof aggregation
- [x] Phase 8 authorization only on PHASE7_COMPLETE

## Closure Evidence — Not Fabricated

- [ ] Discovery gate PASS with real evidence
- [ ] Pilot Exit PASS with real evidence
- [ ] Release Gate 1 PASS with real evidence
- [ ] Release Gate 2 PASS with real evidence
- [ ] Release Gate 3 PASS with real evidence
- [ ] Operational Readiness evidence available
- [ ] Public MVP First-90-Day Gate PASS
- [ ] PHASE7_COMPLETE decision

"""
    if marker not in impl:
        raise SystemExit(
            "ERROR: implementation status insertion marker missing"
        )

    impl = impl.replace(
        marker,
        insert + marker,
        1,
    )

impl = impl.replace(
    "## Current Next Work\n\nPhase 7 evidence ingestion + PMF decision/closure gate.",
    "## Current Next Work\n\nCollect/import real Phase 7 evidence and run the PMF closure gate; Phase 8 remains blocked.",
)

impl_path.write_text(
    impl,
    encoding="utf-8",
)

print("OK: Phase 7 evidence ingestion ledger installed.")
print("OK: Public MVP 90-day evidence gate installed.")
print("OK: PMF closure gate requires non-fixture bound evidence.")
print("STATUS: PHASE 7 EVIDENCE INGESTION + PMF DECISION GATE READY")
print("STATUS: PHASE 7 NOT COMPLETE — REAL EVIDENCE REQUIRED")
