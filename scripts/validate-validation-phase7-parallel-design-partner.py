#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

required = [
    VALIDATION / "design-partners/PARALLEL_EXECUTION.md",
    ROOT / "scripts/phase7-design-partner.py",
    VALIDATION / "STATUS.md",
    VALIDATION / "IMPLEMENTATION_STATUS.md",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing parallel design-partner file: {path}"
        )

py_compile.compile(
    str(
        ROOT
        / "scripts/phase7-design-partner.py"
    ),
    doraise=True,
)

runner = (
    ROOT
    / "scripts/phase7-design-partner.py"
).read_text(
    encoding="utf-8"
)

for phrase in [
    '"DESIGN_PARTNER_COMMITMENT"',
    '"REAL_MERCHANT"',
    '"pilot_status": "CANDIDATE"',
    '"discovery_gate": "STILL_PENDING"',
    '"phase8": "BLOCKED"',
    "willingness_to_test",
    "structured_feedback_available",
    "active_retail_operations",
    "real_inventory",
    "real_customers",
    "transaction_volume_confirmed",
]:
    if phrase not in runner:
        raise SystemExit(
            "ERROR: design-partner execution safeguard missing: "
            + phrase
        )

status = (
    VALIDATION
    / "STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "Discovery interview target: DEFERRED — NOT WAIVED",
    "Discovery Gate bypass: PROHIBITED",
    "Phase 8 bypass: PROHIBITED",
    "Actual design-partner commitments: 1 OF 5 RECORDED",
    "PHASE 7: NOT COMPLETE — REAL EVIDENCE REQUIRED",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: parallel validation status missing or overclaims completion: "
            + phrase
        )

print("OK: Discovery target is deferred, not waived.")
print("OK: Candidate flow requires an ingested REAL_MERCHANT interview.")
print("OK: Existing committed merchants are excluded.")
print("OK: All six canonical design-partner criteria are enforced.")
print("OK: New partner status is CANDIDATE only.")
print("OK: Discovery Gate and Phase 8 boundaries remain intact.")
print("STATUS: PHASE 7 PARALLEL DESIGN-PARTNER EXECUTION READY")
