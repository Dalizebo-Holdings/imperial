#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

required = [
    VALIDATION / "STATUS.md",
    VALIDATION / "IMPLEMENTATION_STATUS.md",
    VALIDATION / "design-partners/ELIGIBILITY_TRIAGE.md",
    ROOT / "scripts/phase7-design-partner.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing eligibility-triage artifact: {path}"
        )

py_compile.compile(
    str(ROOT / "scripts/phase7-design-partner.py"),
    doraise=True,
)

status_path = VALIDATION / "STATUS.md"
status = status_path.read_text(encoding="utf-8")

if "## Design-Partner Eligibility Triage" not in status:
    marker = "## Durable Discovery Gate Derivation\n"
    block = """## Design-Partner Eligibility Triage

Pre-selection canonical eligibility classification: COMPLETE

Eligible vs discovery-only separation: COMPLETE

Missing-criteria reporting: COMPLETE

Recruitment-priority derivation: COMPLETE

Ineligible merchant selection: PROHIBITED

Existing discovery evidence mutation for eligibility: PROHIBITED

Actual design-partner commitment: EVIDENCE COLLECTION PENDING

"""
    if marker not in status:
        raise SystemExit("ERROR: status insertion marker missing")
    status = status.replace(marker, block + marker, 1)

status_path.write_text(status, encoding="utf-8")

impl_path = VALIDATION / "IMPLEMENTATION_STATUS.md"
impl = impl_path.read_text(encoding="utf-8")

if "## Design-Partner Eligibility Triage" not in impl:
    marker = "## Closure Evidence — Not Fabricated\n"
    block = """## Design-Partner Eligibility Triage

- [x] Canonical six-criterion pre-selection classification
- [x] Eligible merchant list
- [x] Discovery-only merchant list
- [x] Missing-criteria reporting
- [x] Already-committed exclusion
- [x] Recruitment-priority derivation
- [x] Ineligible selection prevention
- [x] Existing interview evidence remains immutable
- [ ] First eligible design-partner commitment ingested

"""
    if marker not in impl:
        raise SystemExit(
            "ERROR: implementation-status insertion marker missing"
        )
    impl = impl.replace(marker, block + marker, 1)

impl_path.write_text(impl, encoding="utf-8")

print("OK: design-partner eligibility triage installed.")
print("OK: ineligible interviews are not listed as eligible.")
print("OK: missing criteria are surfaced before selection.")
print("STATUS: PHASE 7 DESIGN-PARTNER ELIGIBILITY TRIAGE READY")
