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
    VALIDATION / "feedback/README.md",
    VALIDATION / "support/README.md",
    VALIDATION / "incidents/README.md",
    VALIDATION / "feedback/FEEDBACK_CONTRACT.md",
    VALIDATION / "support/SUPPORT_CONTRACT.md",
    VALIDATION / "incidents/INCIDENT_CONTRACT.md",
    VALIDATION / "operations_runtime.py",
    VALIDATION / "pilot_runtime.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Phase 7 operational-evidence prerequisite/artifact: {path}"
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
    "Pilot onboarding + validation metrics + release-gate evidence system initialized.",
    "Feedback + Support + Incident evidence system.",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: prior Phase 7 slice not confirmed: "
            + phrase
        )

for path in [
    VALIDATION / "pilot_runtime.py",
    VALIDATION / "operations_runtime.py",
]:
    py_compile.compile(
        str(path),
        doraise=True,
    )

new_status = status.replace(
    "## Current Stage\n\nPilot onboarding + validation metrics + release-gate evidence system initialized.",
    "## Current Stage\n\nFeedback + Support + Incident evidence system initialized.",
)

new_status = new_status.replace(
    "## Next Work\n\nFeedback + Support + Incident evidence system.",
    """## Feedback

Canonical feedback categories: COMPLETE

Structured classification contract: COMPLETE

Evidence-backed product decisions: COMPLETE

Actual merchant feedback: EVIDENCE COLLECTION PENDING

## Support

P0–P3 support evidence registry: COMPLETE

P1 first-response <=1 business day calculation: COMPLETE

Ticket lifecycle + resolution evidence: COMPLETE

Actual support SLA outcomes: EVIDENCE COLLECTION PENDING

## Incidents

Production incident evidence registry: COMPLETE

Critical incident owner enforcement: COMPLETE

Recovery validation + corrective-action closure: COMPLETE

Material tenant-isolation defect tracking: COMPLETE

Actual incident/recovery outcomes: EVIDENCE COLLECTION PENDING

## Operational Evidence

Support process evidence derivation: COMPLETE

Recovery evidence derivation: COMPLETE

Unresolved material tenant-isolation blocker: COMPLETE

Release-gate attestation still requires real evidence references: ENFORCED

## Next Work

Phase 7 evidence ingestion + PMF decision/closure gate.""",
)

status_path.write_text(
    new_status,
    encoding="utf-8",
)

impl_path = (
    VALIDATION
    / "IMPLEMENTATION_STATUS.md"
)
impl = impl_path.read_text(
    encoding="utf-8"
)

if (
    "## Feedback + Support + Incidents"
    not in impl
):
    insert = """## Feedback + Support + Incidents

- [x] Canonical feedback categories
- [x] Feedback classification contract
- [x] Evidence-backed product decision changes
- [x] Feedback immutability/idempotency
- [x] P0/P1/P2/P3 support severity
- [x] Support ownership
- [x] Support first-response evidence
- [x] P1 <=1 business-day calculation
- [x] Support resolution evidence
- [x] Production incident evidence
- [x] Critical incident owner enforcement
- [x] Incident mitigation lifecycle
- [x] Root-cause/resolution/recovery/corrective-action closure
- [x] Material tenant-isolation defect tracking
- [x] Operational readiness evidence digest
- [x] Sensitive credential/payment metadata rejection

## External Operational Evidence — Not Fabricated

- [ ] Merchant feedback recorded
- [ ] Actual P1 response SLA measured
- [ ] Support process demonstrated
- [ ] Recovery procedure demonstrated
- [ ] No unresolved material tenant-isolation defect
- [ ] Operational evidence attached to release gates

"""
    marker = "## External Evidence — Not Fabricated\n"
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
    "## Current Next Work\n\nFeedback + Support + Incident evidence system.",
    "## Current Next Work\n\nPhase 7 evidence ingestion + PMF decision/closure gate.",
)

impl_path.write_text(
    impl,
    encoding="utf-8",
)

print("OK: Phase 7 Feedback + Support + Incident evidence installed.")
print("OK: P1 business-day response and incident recovery evidence installed.")
print("OK: Material tenant-isolation operational blocker installed.")
print("STATUS: PHASE 7 FEEDBACK + SUPPORT + INCIDENTS READY")
print("NEXT: Phase 7 evidence ingestion + PMF decision/closure gate.")
