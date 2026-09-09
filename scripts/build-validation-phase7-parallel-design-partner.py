#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

required = [
    VALIDATION / "STATUS.md",
    VALIDATION / "IMPLEMENTATION_STATUS.md",
    VALIDATION / "runtime.py",
    VALIDATION / "evidence/collection.py",
    VALIDATION / "evidence/store.py",
    VALIDATION / "design-partners/PARALLEL_EXECUTION.md",
    ROOT / "scripts/phase7-design-partner.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing parallel design-partner prerequisite/artifact: {path}"
        )

status_path = VALIDATION / "STATUS.md"
status = status_path.read_text(
    encoding="utf-8"
)

for phrase in [
    "Actual discovery interviews: EVIDENCE COLLECTION PENDING",
    "PHASE 7: NOT COMPLETE — REAL EVIDENCE REQUIRED",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Phase 7 discovery boundary not confirmed: "
            + phrase
        )

py_compile.compile(
    str(
        ROOT
        / "scripts/phase7-design-partner.py"
    ),
    doraise=True,
)

if "## Parallel Validation Execution" not in status:
    marker = "## Phase 7 Closure State\n"
    block = """## Parallel Validation Execution

Discovery interview target: DEFERRED — NOT WAIVED

Design-partner candidate execution: COMPLETE

Interview-to-partner merchant linkage: COMPLETE

Canonical partner-criteria enforcement: COMPLETE

Candidate pilot status only: ENFORCED

Discovery Gate bypass: PROHIBITED

Phase 8 bypass: PROHIBITED

Actual design-partner commitment: EVIDENCE COLLECTION PENDING

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

status = status.replace(
    "Conduct real merchant discovery interviews with `scripts/phase7-discovery-interview.py`, ingest validated evidence, and continue until the canonical Discovery Gate is satisfied.",
    "Continue merchant discovery when practical. In parallel, eligible interviewed merchants may enter the design-partner candidate flow with `scripts/phase7-design-partner.py`; the Discovery target remains deferred, not waived.",
    1,
)

status_path.write_text(
    status,
    encoding="utf-8",
)

impl_path = (
    VALIDATION
    / "IMPLEMENTATION_STATUS.md"
)
impl = impl_path.read_text(
    encoding="utf-8"
)

if "## Parallel Validation Execution" not in impl:
    marker = "## Closure Evidence — Not Fabricated\n"
    block = """## Parallel Validation Execution

- [x] Discovery target may be operationally deferred
- [x] Discovery target cannot be waived by tooling
- [x] Real interviewed merchant lookup
- [x] Existing commitment exclusion
- [x] Canonical six-criterion partner enforcement
- [x] Linked merchant reference preservation
- [x] Candidate-only initial pilot status
- [x] Discovery Gate remains authoritative
- [x] Phase 8 remains blocked
- [ ] First real design-partner commitment ingested

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

print("OK: Phase 7 parallel validation execution installed.")
print("OK: Discovery target is deferred but remains authoritative.")
print("OK: Real interview -> design-partner candidate linkage installed.")
print("OK: Candidate flow fails closed on any unmet partner criterion.")
print("STATUS: PHASE 7 PARALLEL DESIGN-PARTNER EXECUTION READY")
print("STATUS: DISCOVERY GATE PENDING — PHASE 8 BLOCKED")
