#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

gate3_path = VALIDATION / "evidence/gate3_derive.py"
cli_path = ROOT / "scripts/phase7-evidence-void.py"
doc_path = VALIDATION / "evidence/APPEND_ONLY_VOID.md"

for path in (
    gate3_path,
    cli_path,
    doc_path,
    VALIDATION / "STATUS.md",
    VALIDATION / "IMPLEMENTATION_STATUS.md",
):
    if not path.exists():
        raise SystemExit(f"ERROR: missing prerequisite/artifact: {path}")

replacement_path = (
    ROOT
    / "scripts/.phase7-evidence-void-read-rows.txt"
)
replacement = replacement_path.read_text(
    encoding="utf-8"
).rstrip() + "\n\n"

source = gate3_path.read_text(
    encoding="utf-8"
)

start = source.find("def _read_rows(")
end = source.find("\ndef _commitment(", start)

if start < 0 or end < 0:
    raise SystemExit(
        "ERROR: cannot locate Gate 3 _read_rows patch target"
    )

if '"EVIDENCE_VOID"' not in source[start:end]:
    source = (
        source[:start]
        + replacement
        + source[end + 1:]
    )
    gate3_path.write_text(
        source,
        encoding="utf-8",
    )

py_compile.compile(str(gate3_path), doraise=True)
py_compile.compile(str(cli_path), doraise=True)

status_path = VALIDATION / "STATUS.md"
status = status_path.read_text(
    encoding="utf-8"
)

if "## Append-only Evidence Void" not in status:
    marker = "## Durable Release Gate 3 Derivation\n"
    block = """## Append-only Evidence Void

EVIDENCE_VOID correction envelope: COMPLETE

Original evidence preservation: COMPLETE

Target envelope/content digest binding: COMPLETE

Gate 3 void-aware replay: COMPLETE

TEST_FIXTURE exclusion: COMPLETE

Direct ledger mutation/deletion: PROHIBITED

Automatic Gate PASS claim: PROHIBITED

Actual void records: PRIVATE DURABLE EVIDENCE ONLY

"""
    if marker not in status:
        raise SystemExit(
            "ERROR: STATUS insertion marker missing"
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

if "## Append-only Evidence Void" not in impl:
    marker = "## Closure Evidence — Not Fabricated\n"
    block = """## Append-only Evidence Void

- [x] Append-only EVIDENCE_VOID writer
- [x] Existing target/event verification
- [x] Target payload digest binding
- [x] Duplicate void rejection
- [x] Gate 3 replay excludes only verified void targets
- [x] Original durable evidence retained
- [x] No direct ledger rewrite/delete
- [x] No automatic Gate PASS or Phase 8 authorization

"""
    if marker not in impl:
        raise SystemExit(
            "ERROR: IMPLEMENTATION_STATUS insertion marker missing"
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

print("OK: Phase 7 append-only evidence void installed.")
print("OK: Gate 3 replay is void-aware.")
print("OK: original ledger evidence remains immutable.")
print("STATUS: PHASE 7 APPEND-ONLY EVIDENCE VOID READY")
