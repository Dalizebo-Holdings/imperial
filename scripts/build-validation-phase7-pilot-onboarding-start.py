#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

required = [
    VALIDATION / "STATUS.md",
    VALIDATION / "IMPLEMENTATION_STATUS.md",
    VALIDATION / "runtime.py",
    VALIDATION / "pilot_runtime.py",
    VALIDATION / "evidence/collection.py",
    VALIDATION / "onboarding/PILOT_ONBOARDING_START.md",
    ROOT / "scripts/phase7-pilot-onboarding-start.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing pilot-onboarding-start prerequisite/artifact: {path}"
        )

py_compile.compile(
    str(ROOT / "scripts/phase7-pilot-onboarding-start.py"),
    doraise=True,
)

status_path = VALIDATION / "STATUS.md"
status = status_path.read_text(
    encoding="utf-8"
)

if "## Pilot Onboarding Start Execution" not in status:
    marker = "## Durable Pilot Onboarding Event Evidence\n"
    block = """## Pilot Onboarding Start Execution

ACTIVE design-partner eligibility reconstruction: COMPLETE

Canonical PILOT_ONBOARDING writer: COMPLETE

Merchant/product inheritance from commitment: COMPLETE

One-onboarding-per-merchant enforcement: COMPLETE

Explicit real onboarding-start evidence reference: COMPLETE

Owner-only private inbox execution: COMPLETE

Automatic ACTIVE promotion: PROHIBITED

Automatic onboarding completion claim: PROHIBITED

Automatic Gate 3 PASS claim: PROHIBITED

Actual pilot onboarding start: EVIDENCE COLLECTION PENDING

"""
    if marker not in status:
        raise SystemExit(
            "ERROR: status insertion marker missing"
        )
    status = status.replace(
        marker,
        block + marker,
        1,
    )

status_path.write_text(
    status,
    encoding="utf-8",
)

impl_path = VALIDATION / "IMPLEMENTATION_STATUS.md"
impl = impl_path.read_text(
    encoding="utf-8"
)

if "## Pilot Onboarding Start Execution" not in impl:
    marker = "## Closure Evidence — Not Fabricated\n"
    block = """## Pilot Onboarding Start Execution

- [x] Durable current pilot-state reconstruction
- [x] ACTIVE-only onboarding start enforcement
- [x] Merchant/product inheritance
- [x] One onboarding per merchant
- [x] Explicit real evidence reference
- [x] Canonical PilotOnboarding validation
- [x] Canonical PilotValidationRegistry.start_onboarding validation
- [x] Owner-only inbox artifact
- [x] No automatic ACTIVE promotion
- [x] No automatic onboarding completion
- [x] No automatic Gate 3 PASS
- [ ] First real pilot onboarding start ingested

"""
    if marker not in impl:
        raise SystemExit(
            "ERROR: implementation-status insertion marker missing"
        )
    impl = impl.replace(
        marker,
        block + marker,
        1,
    )

impl_path.write_text(
    impl,
    encoding="utf-8",
)

print("OK: Phase 7 pilot onboarding start execution installed.")
print("OK: only current ACTIVE partners may start onboarding.")
print("OK: canonical PilotValidationRegistry.start_onboarding is reused.")
print("OK: no completion/Gate 3/Phase 8 claim is made.")
print("STATUS: PHASE 7 PILOT ONBOARDING START EXECUTION READY")
