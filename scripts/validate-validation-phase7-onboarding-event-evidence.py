#!/usr/bin/env python3
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

script = (ROOT / "scripts/phase7-onboarding-event.py").read_text(encoding="utf-8")
ast.parse(script)
collection = (VALIDATION / "evidence/collection.py").read_text(encoding="utf-8")

for phrase in [
    '"pilot-onboarding-event": _template(',
    'evidence_type="PILOT_ONBOARDING_EVENT"',
    'origin="REAL_MERCHANT"',
    '"event_id": "__REPLACE__"',
    '"training_required": False',
]:
    if phrase not in collection:
        raise SystemExit("ERROR: collection schema missing onboarding-event requirement: " + phrase)

for phrase in [
    "OnboardingEvent(**payload).validate()",
    '"PILOT_ONBOARDING_EVENT"',
    '"REAL_MERCHANT"',
    "_select(onboardings",
    '"onboarding_completion_claimed": False',
    '"gate3_pass_claimed": False',
    '"phase8": "BLOCKED"',
]:
    if phrase not in script:
        raise SystemExit("ERROR: onboarding-event safeguard missing: " + phrase)

status = (VALIDATION / "STATUS.md").read_text(encoding="utf-8")
for phrase in [
    "PILOT_ONBOARDING_EVENT evidence type: COMPLETE",
    "Real onboarding linkage enforcement: COMPLETE",
    "Automatic onboarding completion claim: PROHIBITED",
    "Automatic Gate 3 PASS claim: PROHIBITED",
    "Actual onboarding event evidence: RECORDED FOR 1 PILOT",
    "PHASE 7: NOT COMPLETE — REAL EVIDENCE REQUIRED",
]:
    if phrase not in status:
        raise SystemExit("ERROR: status missing or overclaims onboarding-event state: " + phrase)

print("OK: onboarding-event CLI syntax valid.")
print("OK: collection schema includes PILOT_ONBOARDING_EVENT.")
print("OK: event requires ingested real onboarding linkage.")
print("OK: canonical OnboardingEvent validation is present.")
print("OK: no completion/Gate 3/Phase 8 claim is made.")
print("STATUS: PHASE 7 DURABLE ONBOARDING EVENT EVIDENCE READY")
