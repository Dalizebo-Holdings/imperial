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
    VALIDATION / "evidence/runtime.py",
    VALIDATION / "evidence/store.py",
    VALIDATION / "evidence/collection.py",
    VALIDATION / "evidence/REAL_EVIDENCE_COLLECTION.md",
    ROOT / "scripts/validation-evidence.py",
    ROOT / "scripts/evaluate-phase7-pmf.py",
    ROOT / "scripts/phase7-evidence-collect.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Phase 7 collection prerequisite/artifact: {path}"
        )

status_path = VALIDATION / "STATUS.md"
status = status_path.read_text(
    encoding="utf-8"
)

for phrase in [
    "Durable evidence ledger: COMPLETE",
    "Actual real evidence imported: PENDING",
    "PHASE 7: NOT COMPLETE — REAL EVIDENCE REQUIRED",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Phase 7 real-evidence operations not confirmed: "
            + phrase
        )

for path in [
    VALIDATION / "evidence/runtime.py",
    VALIDATION / "evidence/store.py",
    VALIDATION / "evidence/collection.py",
    ROOT / "scripts/validation-evidence.py",
    ROOT / "scripts/evaluate-phase7-pmf.py",
    ROOT / "scripts/phase7-evidence-collect.py",
]:
    py_compile.compile(
        str(path),
        doraise=True,
    )

if "## Real Evidence Collection Kit" not in status:
    marker = "## Phase 7 Closure State\n"
    block = """## Real Evidence Collection Kit

Private evidence inbox: COMPLETE

Domain evidence templates: COMPLETE

Placeholder rejection: COMPLETE

Batch preflight validation: COMPLETE

Replay-safe batch ingestion: COMPLETE

Evidence progress reporting: COMPLETE

Real evidence auto-fabrication: PROHIBITED

Actual real evidence imported: PENDING

"""
    if marker not in status:
        raise SystemExit(
            "ERROR: Phase 7 status insertion marker missing"
        )
    status = status.replace(
        marker,
        block + marker,
        1,
    )

status = status.replace(
    "Use the durable evidence CLI to collect/import real Phase 7 evidence and execute the PMF closure gate. Phase 8 remains blocked until `PHASE7_COMPLETE`.",
    "Initialize the private evidence inbox, replace template placeholders with real source-backed evidence, batch-ingest it, then execute the PMF closure gate. Phase 8 remains blocked until `PHASE7_COMPLETE`.",
)

status_path.write_text(
    status,
    encoding="utf-8",
)

impl_path = VALIDATION / "IMPLEMENTATION_STATUS.md"
impl = impl_path.read_text(
    encoding="utf-8"
)

if "## Real Evidence Collection Kit" not in impl:
    marker = "## Closure Evidence — Not Fabricated\n"
    block = """## Real Evidence Collection Kit

- [x] Private non-Git evidence inbox
- [x] Discovery interview template
- [x] Design-partner commitment template
- [x] Pilot onboarding template
- [x] Pilot metric snapshot template
- [x] Capacity snapshot template
- [x] Technical attestation template
- [x] Merchant feedback template
- [x] Support evidence template
- [x] Incident evidence template
- [x] Public MVP 90-day template
- [x] Gate-proof template
- [x] Placeholder rejection
- [x] Whole-inbox preflight
- [x] Replay-safe batch ingestion
- [x] Evidence progress report
- [ ] Real Phase 7 evidence imported

"""
    if marker not in impl:
        raise SystemExit(
            "ERROR: implementation status insertion marker missing"
        )
    impl = impl.replace(
        marker,
        block + marker,
        1,
    )

impl = impl.replace(
    "Use the durable evidence CLI to collect/import real Phase 7 evidence and run the PMF closure gate; Phase 8 remains blocked.",
    "Initialize the private evidence inbox, ingest real source-backed evidence, and run the PMF closure gate; Phase 8 remains blocked.",
)

impl_path.write_text(
    impl,
    encoding="utf-8",
)

print("OK: Phase 7 private real-evidence collection inbox installed.")
print("OK: Domain templates + placeholder rejection installed.")
print("OK: Whole-inbox preflight + replay-safe batch ingestion installed.")
print("OK: Evidence progress reporting installed.")
print("STATUS: PHASE 7 REAL EVIDENCE COLLECTION KIT READY")
print("STATUS: PHASE 7 NOT COMPLETE — REAL EVIDENCE REQUIRED")
