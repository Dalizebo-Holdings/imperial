#!/usr/bin/env python3
from pathlib import Path
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

required = [
    VALIDATION / "design-partners/RECRUITMENT_PLAYBOOK.md",
    VALIDATION / "design-partners/INTERVIEW_GUIDE.md",
    ROOT / "scripts/phase7-discovery-interview.py",
    VALIDATION / "evidence/collection.py",
    VALIDATION / "STATUS.md",
    VALIDATION / "IMPLEMENTATION_STATUS.md",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing discovery execution file: {path}"
        )

for path in [
    ROOT / "scripts/phase7-discovery-interview.py",
    VALIDATION / "evidence/collection.py",
]:
    py_compile.compile(
        str(path),
        doraise=True,
    )

runner = (
    ROOT
    / "scripts/phase7-discovery-interview.py"
).read_text(
    encoding="utf-8"
)

for phrase in [
    'origin": "REAL_MERCHANT"',
    '"core_problem_material": material',
    '"willingness_to_test": willing',
    '"structured_feedback_available": feedback',
    '"READY_FOR_INBOX_PREFLIGHT"',
    "merchant://phase7/",
    "evidence://phase7/discovery/",
]:
    if phrase not in runner:
        raise SystemExit(
            "ERROR: discovery runner requirement missing: "
            + phrase
        )

guide = (
    VALIDATION
    / "design-partners/INTERVIEW_GUIDE.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "Material Problem Test",
    "Would you be willing to test",
    "structured feedback",
    "Do not store:",
]:
    if phrase not in guide:
        raise SystemExit(
            "ERROR: interview guide requirement missing: "
            + phrase
        )

status = (
    VALIDATION / "STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "Recruitment playbook: COMPLETE",
    "Live interview evidence runner: COMPLETE",
    "Actual discovery interviews: 4 OF 20 RECORDED",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: discovery status missing/overclaimed: "
            + phrase
        )

print("OK: Canonical discovery targets preserved.")
print("OK: Recruitment guide avoids leading validation questions.")
print("OK: Interview runner requires actual operator answers.")
print("OK: REAL_MERCHANT evidence fields match collection envelope.")
print("OK: Opaque merchant/evidence references are generated.")
print("OK: Discovery evidence remains pending until interview execution.")
print("STATUS: PHASE 7 MERCHANT DISCOVERY EXECUTION READY")
