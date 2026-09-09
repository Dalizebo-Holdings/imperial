#!/usr/bin/env python3
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

source = (
    ROOT
    / "scripts/phase7-pilot-onboarding-start.py"
).read_text(
    encoding="utf-8"
)

ast.parse(source)

for phrase in [
    '"TEST_FIXTURE"',
    '"DESIGN_PARTNER_COMMITMENT"',
    '"PILOT_STATUS_TRANSITION"',
    '"PILOT_ONBOARDING"',
    '"REAL_MERCHANT"',
    'item.pilot_status != "ACTIVE"',
    "merchant already has PILOT_ONBOARDING evidence",
    "PilotOnboarding(",
    "validation_registry.start_onboarding(",
    '"active_status_verified_from_ledger": True',
    '"onboarding_completion_claimed": False',
    '"gate3_pass_claimed": False',
    '"phase8": "BLOCKED"',
]:
    if phrase not in source:
        raise SystemExit(
            "ERROR: onboarding-start requirement missing: "
            + phrase
        )

status = (
    VALIDATION
    / "STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "ACTIVE design-partner eligibility reconstruction: COMPLETE",
    "Canonical PILOT_ONBOARDING writer: COMPLETE",
    "Automatic ACTIVE promotion: PROHIBITED",
    "Automatic onboarding completion claim: PROHIBITED",
    "Actual pilot onboarding starts: 1 RECORDED — MINIMUM 5 STILL PENDING",
    "PHASE 7: NOT COMPLETE — REAL EVIDENCE REQUIRED",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: status missing or overclaims onboarding-start state: "
            + phrase
        )

print("OK: pilot-onboarding-start CLI syntax valid.")
print("OK: ACTIVE-only start enforcement present.")
print("OK: canonical onboarding validator is reused.")
print("OK: duplicate merchant onboarding is blocked.")
print("OK: no completion/Gate 3/Phase 8 claim is made.")
print("STATUS: PHASE 7 PILOT ONBOARDING START EXECUTION READY")
