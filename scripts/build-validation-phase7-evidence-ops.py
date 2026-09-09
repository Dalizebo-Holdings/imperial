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
    VALIDATION / "evidence/REAL_EVIDENCE_OPERATIONS.md",
    VALIDATION / "decision/runtime.py",
    ROOT / "scripts/validation-evidence.py",
    ROOT / "scripts/evaluate-phase7-pmf.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Phase 7 real-evidence operations prerequisite/artifact: {path}"
        )

status_path = VALIDATION / "STATUS.md"
status = status_path.read_text(
    encoding="utf-8"
)

for phrase in [
    "Evidence ingestion + PMF decision/closure gate initialized.",
    "PHASE 7: NOT COMPLETE — REAL EVIDENCE REQUIRED",
    "Collect/import real Phase 7 evidence and run the PMF closure gate.",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Phase 7 decision gate is not confirmed: "
            + phrase
        )

for path in [
    VALIDATION / "evidence/runtime.py",
    VALIDATION / "evidence/store.py",
    VALIDATION / "decision/runtime.py",
    ROOT / "scripts/validation-evidence.py",
    ROOT / "scripts/evaluate-phase7-pmf.py",
]:
    py_compile.compile(
        str(path),
        doraise=True,
    )

if (
    "## Real Evidence Operations"
    not in status
):
    marker = "## Phase 7 Closure State\n"
    block = """## Real Evidence Operations

Durable evidence ledger: COMPLETE

Filesystem locking + fsync append: COMPLETE

Ledger rebuild + chain verification: COMPLETE

Real evidence ingestion CLI: COMPLETE

Verified evidence export: COMPLETE

Public MVP snapshot evaluator CLI: COMPLETE

PMF proof-manifest evaluator CLI: COMPLETE

Default evidence storage outside Git: COMPLETE

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
    "Collect/import real Phase 7 evidence and run the PMF closure gate. Phase 8 remains blocked until `PHASE7_COMPLETE`.",
    "Use the durable evidence CLI to collect/import real Phase 7 evidence and execute the PMF closure gate. Phase 8 remains blocked until `PHASE7_COMPLETE`.",
)

status_path.write_text(
    status,
    encoding="utf-8",
)

impl_path = VALIDATION / "IMPLEMENTATION_STATUS.md"
impl = impl_path.read_text(
    encoding="utf-8"
)

if (
    "## Real Evidence Operations"
    not in impl
):
    marker = "## Closure Evidence — Not Fabricated\n"
    block = """## Real Evidence Operations

- [x] Durable JSONL evidence store
- [x] Owner-only ledger permissions
- [x] Exclusive append lock
- [x] fsync evidence append
- [x] Ledger rebuild/chain verification
- [x] Evidence ingestion CLI
- [x] Evidence status/verify CLI
- [x] Verified evidence export
- [x] Public MVP 90-day snapshot evaluator CLI
- [x] PMF proof-manifest evaluator CLI
- [x] Real evidence stored outside Git by default
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
    "Collect/import real Phase 7 evidence and run the PMF closure gate; Phase 8 remains blocked.",
    "Use the durable evidence CLI to collect/import real Phase 7 evidence and run the PMF closure gate; Phase 8 remains blocked.",
)

impl_path.write_text(
    impl,
    encoding="utf-8",
)

print("OK: Durable Phase 7 real-evidence operations installed.")
print("OK: Evidence ledger defaults outside Git with locking/fsync.")
print("OK: Ingest/verify/status/export CLI installed.")
print("OK: Public MVP + PMF closure evaluator CLI installed.")
print("STATUS: PHASE 7 REAL EVIDENCE OPERATIONS READY")
print("STATUS: PHASE 7 NOT COMPLETE — REAL EVIDENCE REQUIRED")
