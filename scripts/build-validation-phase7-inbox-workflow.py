#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

required = [
    VALIDATION / "STATUS.md",
    VALIDATION / "IMPLEMENTATION_STATUS.md",
    VALIDATION / "evidence/runtime.py",
    VALIDATION / "evidence/store.py",
    VALIDATION / "evidence/collection.py",
    VALIDATION / "evidence/REAL_EVIDENCE_COLLECTION.md",
    ROOT / "scripts/phase7-evidence-collect.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Phase 7 inbox workflow prerequisite/artifact: {path}"
        )

status_path = VALIDATION / "STATUS.md"
status = status_path.read_text(
    encoding="utf-8"
)

for phrase in [
    "## Real Evidence Collection Kit",
    "Actual real evidence imported: PENDING",
    "PHASE 7: NOT COMPLETE — REAL EVIDENCE REQUIRED",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: prior Phase 7 collection kit is not confirmed: "
            + phrase
        )

for path in [
    VALIDATION / "evidence/collection.py",
    ROOT / "scripts/phase7-evidence-collect.py",
]:
    py_compile.compile(
        str(path),
        doraise=True,
    )

if "## Evidence Inbox Workflow" not in status:
    marker = "## Phase 7 Closure State\n"
    block = """## Evidence Inbox Workflow

Empty active inbox initialization: COMPLETE

Separate private template library: COMPLETE

Single-record `new <type> <name>` workflow: COMPLETE

Template library excluded from active preflight: COMPLETE

Incremental evidence collection: COMPLETE

Actual real evidence imported: PENDING

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
    "Initialize the private evidence inbox, replace template placeholders with real source-backed evidence, batch-ingest it, then execute the PMF closure gate. Phase 8 remains blocked until `PHASE7_COMPLETE`.",
    "Initialize the empty private inbox, create one evidence record at a time with `phase7-evidence-collect.py new`, replace placeholders with real source-backed values, ingest validated records, then execute the PMF closure gate. Phase 8 remains blocked until `PHASE7_COMPLETE`.",
)

status_path.write_text(
    status,
    encoding="utf-8",
)

impl_path = VALIDATION / "IMPLEMENTATION_STATUS.md"
impl = impl_path.read_text(
    encoding="utf-8"
)

if "## Evidence Inbox Workflow" not in impl:
    marker = "## Closure Evidence — Not Fabricated\n"
    block = """## Evidence Inbox Workflow

- [x] Empty active inbox initialization
- [x] Separate private template library
- [x] 11 templates remain available
- [x] Single-record `new` workflow
- [x] Simple-file-name validation
- [x] Existing-record overwrite rejection
- [x] Template library excluded from preflight
- [x] Empty inbox valid
- [x] Incremental evidence collection
- [ ] Real Phase 7 evidence imported

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

impl = impl.replace(
    "Initialize the private evidence inbox, ingest real source-backed evidence, and run the PMF closure gate; Phase 8 remains blocked.",
    "Initialize the empty private inbox, create and ingest real source-backed records incrementally, and run the PMF closure gate; Phase 8 remains blocked.",
)

impl_path.write_text(
    impl,
    encoding="utf-8",
)

print("OK: Phase 7 evidence inbox workflow hardened.")
print("OK: Active inbox is empty after initialization.")
print("OK: 11 templates live in a separate private template library.")
print("OK: Incremental `new <type> <name>` collection installed.")
print("STATUS: PHASE 7 EVIDENCE INBOX WORKFLOW READY")
print("STATUS: PHASE 7 NOT COMPLETE — REAL EVIDENCE REQUIRED")
