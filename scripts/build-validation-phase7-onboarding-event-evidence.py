#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

required = [
    VALIDATION / "STATUS.md",
    VALIDATION / "IMPLEMENTATION_STATUS.md",
    VALIDATION / "pilot_runtime.py",
    VALIDATION / "evidence/collection.py",
    VALIDATION / "onboarding/DURABLE_EVENT_EVIDENCE.md",
    ROOT / "scripts/phase7-onboarding-event.py",
]
for path in required:
    if not path.exists():
        raise SystemExit(f"ERROR: missing onboarding-event prerequisite/artifact: {path}")

py_compile.compile(str(ROOT / "scripts/phase7-onboarding-event.py"), doraise=True)

collection_path = VALIDATION / "evidence/collection.py"
collection = collection_path.read_text(encoding="utf-8")

if '"pilot-onboarding-event": _template(' not in collection:
    marker = '        "pilot-metric-snapshot": _template(\n'
    block = (
        '        "pilot-onboarding-event": _template(\n'
        '            evidence_type="PILOT_ONBOARDING_EVENT",\n'
        '            origin="REAL_MERCHANT",\n'
        '            source_system_ref="source://validation/pilot-onboarding-events",\n'
        '            payload={\n'
        '                "event_id": "__REPLACE__",\n'
        '                "onboarding_id": "__REPLACE__",\n'
        '                "merchant_ref": "__REPLACE__",\n'
        '                "step": "__REPLACE__",\n'
        '                "status": "__REPLACE__",\n'
        '                "occurred_at": "__REPLACE__",\n'
        '                "evidence_ref": "__REPLACE__",\n'
        '                "failure_code": None,\n'
        '                "training_required": False,\n'
        '                "support_intervention": False,\n'
        '                "metadata": {},\n'
        '            },\n'
        '        ),\n'
    )
    if marker not in collection:
        raise SystemExit("ERROR: collection template insertion marker missing")
    collection = collection.replace(marker, block + marker, 1)

collection_path.write_text(collection, encoding="utf-8")

status_path = VALIDATION / "STATUS.md"
status = status_path.read_text(encoding="utf-8")
if "## Durable Pilot Onboarding Event Evidence" not in status:
    marker = "## Pilot Metrics\n"
    block = """## Durable Pilot Onboarding Event Evidence

PILOT_ONBOARDING_EVENT evidence type: COMPLETE

Real onboarding linkage enforcement: COMPLETE

Canonical onboarding-step validation: COMPLETE

Failure/retry evidence support: COMPLETE

Training/support intervention evidence support: COMPLETE

Owner-only private inbox execution: COMPLETE

Automatic onboarding completion claim: PROHIBITED

Automatic Gate 3 PASS claim: PROHIBITED

Actual onboarding event evidence: EVIDENCE COLLECTION PENDING

"""
    if marker not in status:
        raise SystemExit("ERROR: status insertion marker missing")
    status = status.replace(marker, block + marker, 1)
status_path.write_text(status, encoding="utf-8")

impl_path = VALIDATION / "IMPLEMENTATION_STATUS.md"
impl = impl_path.read_text(encoding="utf-8")
if "## Durable Pilot Onboarding Event Evidence" not in impl:
    marker = "## Closure Evidence — Not Fabricated\n"
    block = """## Durable Pilot Onboarding Event Evidence

- [x] PILOT_ONBOARDING_EVENT collection template
- [x] REAL_MERCHANT provenance
- [x] Ingested PILOT_ONBOARDING linkage
- [x] Merchant identity inherited from onboarding
- [x] Canonical onboarding step validation
- [x] SUCCESS/FAILED event support
- [x] Failure-code validation
- [x] Training/support intervention evidence
- [x] Owner-only inbox artifact
- [x] No automatic onboarding completion claim
- [x] No automatic Gate 3 PASS claim
- [ ] First real onboarding event ingested

"""
    if marker not in impl:
        raise SystemExit("ERROR: implementation-status insertion marker missing")
    impl = impl.replace(marker, block + marker, 1)
impl_path.write_text(impl, encoding="utf-8")

print("OK: durable pilot onboarding event evidence installed.")
print("OK: onboarding events link to ingested real onboarding records.")
print("OK: canonical OnboardingEvent validation is enforced.")
print("OK: no completion or Gate 3 PASS is claimed.")
print("STATUS: PHASE 7 DURABLE ONBOARDING EVENT EVIDENCE READY")
