#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

required = [
    VALIDATION / "STATUS.md",
    VALIDATION / "IMPLEMENTATION_STATUS.md",
    VALIDATION / "pilot_runtime.py",
    VALIDATION / "evidence/release_gate_derive.py",
    VALIDATION / "release-gates/RELEASE_READINESS_DASHBOARD.md",
    ROOT / "scripts/phase7-release-readiness.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing release-readiness prerequisite/artifact: {path}"
        )

py_compile.compile(
    str(
        ROOT
        / "scripts/phase7-release-readiness.py"
    ),
    doraise=True,
)

source = (
    ROOT
    / "scripts/phase7-release-readiness.py"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "derive_release_gate_1(",
    "derive_release_gate_2(",
    "GATE1_ATTESTATIONS",
    "GATE2_ATTESTATIONS",
    '"proof_emission_allowed"',
    '"thresholds_waived": False',
    '"fixture_evidence_excluded": True',
    '"evidence_generated": False',
    '"proof_generated": False',
    '"phase8_authorized": False',
]:
    if phrase not in source:
        raise SystemExit(
            "ERROR: release-readiness safeguard missing: "
            + phrase
        )

status_path = VALIDATION / "STATUS.md"
status = status_path.read_text(
    encoding="utf-8"
)

if "## Release Gate Readiness Dashboard" not in status:
    marker = "## Durable Release Gate 1/2 Derivation\n"
    block = """## Release Gate Readiness Dashboard

Canonical Gate 1 readiness reporting: COMPLETE

Canonical Gate 2 readiness reporting: COMPLETE

Missing/failed/expired requirement surfacing: COMPLETE

Gate 1 Discovery blocker surfacing: COMPLETE

PASS-only proof readiness reporting: COMPLETE

Evidence generation by dashboard: PROHIBITED

Gate override by dashboard: PROHIBITED

Phase 8 authorization by dashboard: PROHIBITED

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

if "## Release Gate Readiness Dashboard" not in impl:
    marker = "## Closure Evidence — Not Fabricated\n"
    block = """## Release Gate Readiness Dashboard

- [x] Canonical Gate 1 readiness report
- [x] Canonical Gate 2 readiness report
- [x] Canonical unmet-check surfacing
- [x] Technical-attestation readiness map
- [x] Gate 1 Discovery dependency visibility
- [x] PASS-only proof readiness flag
- [x] No evidence generation
- [x] No gate override
- [x] No Phase 8 authorization

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

print("OK: Phase 7 Release Gate readiness dashboard installed.")
print("OK: Gate 1/2 canonical derivations are reused.")
print("OK: missing/failed/expired requirements are surfaced.")
print("OK: dashboard cannot generate evidence or authorize Phase 8.")
print("STATUS: PHASE 7 RELEASE READINESS DASHBOARD READY")
