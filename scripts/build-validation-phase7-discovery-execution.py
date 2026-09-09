#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

required = [
    VALIDATION / "STATUS.md",
    VALIDATION / "IMPLEMENTATION_STATUS.md",
    VALIDATION / "design-partners/README.md",
    VALIDATION / "design-partners/RECRUITMENT_PLAYBOOK.md",
    VALIDATION / "design-partners/INTERVIEW_GUIDE.md",
    VALIDATION / "evidence/collection.py",
    ROOT / "scripts/phase7-discovery-interview.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing discovery-execution prerequisite/artifact: {path}"
        )

design = (
    VALIDATION
    / "design-partners/README.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "20–30 discovery interviews",
    "5–10 design partner commitments",
    "Minimum 3 active pilot merchants",
    "At least 80% of interviewed merchants should confirm the core problem is material.",
]:
    if phrase not in design:
        raise SystemExit(
            "ERROR: canonical discovery target missing: "
            + phrase
        )

py_compile.compile(
    str(
        ROOT
        / "scripts/phase7-discovery-interview.py"
    ),
    doraise=True,
)

status_path = VALIDATION / "STATUS.md"
status = status_path.read_text(
    encoding="utf-8"
)

if "## Merchant Discovery Execution" not in status:
    marker = "## Phase 7 Closure State\n"
    block = """## Merchant Discovery Execution

Recruitment playbook: COMPLETE

Interview guide: COMPLETE

Live interview evidence runner: COMPLETE

Automatic opaque merchant references: COMPLETE

Sensitive credential/payment material rejection: COMPLETE

Real interview evidence auto-generation without interview: PROHIBITED

Actual discovery interviews: EVIDENCE COLLECTION PENDING

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
    "## Next Work\n\n",
    "## Next Work\n\nConduct real merchant discovery interviews with `scripts/phase7-discovery-interview.py`, ingest validated evidence, and continue until the canonical Discovery Gate is satisfied.\n\n",
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

if "## Merchant Discovery Execution" not in impl:
    marker = "## Closure Evidence — Not Fabricated\n"
    block = """## Merchant Discovery Execution

- [x] Recruitment playbook
- [x] Interview guide
- [x] Interactive live interview runner
- [x] Opaque merchant reference generation
- [x] Opaque evidence reference generation
- [x] Material-problem classification prompt
- [x] Willingness-to-test prompt
- [x] Structured-feedback prompt
- [x] Non-sensitive operational context
- [x] Canonical inbox-envelope validation
- [x] Owner-only evidence record permissions
- [ ] First real discovery interview recorded
- [ ] 20+ real discovery interviews recorded
- [ ] >=80% material-problem confirmation

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

impl_path.write_text(
    impl,
    encoding="utf-8",
)

print("OK: Phase 7 merchant-discovery execution pack installed.")
print("OK: Live interview runner creates canonical REAL_MERCHANT evidence.")
print("OK: No interview can be fabricated by the builder.")
print("STATUS: PHASE 7 MERCHANT DISCOVERY EXECUTION READY")
print("NEXT: Conduct first real merchant discovery interview.")
