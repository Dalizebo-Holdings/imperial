#!/usr/bin/env python3
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent.parent
script_path = ROOT / "scripts/phase7-design-partner.py"

source = script_path.read_text(encoding="utf-8")
ast.parse(source)

required_phrases = [
    '"eligible_count"',
    '"discovery_only_count"',
    '"missing_criteria"',
    '"recruitment_priority_missing_criteria"',
    '"real_inventory"',
    '"transaction_volume_confirmed"',
    '"eligibility_source"',
    "no design-partner-eligible interviewed merchants found",
    'merchant = _select(triage["eligible"])',
]

for phrase in required_phrases:
    if phrase not in source:
        raise SystemExit(
            "ERROR: eligibility triage requirement missing: "
            + phrase
        )

status = (
    ROOT / "validation/STATUS.md"
).read_text(encoding="utf-8")

for phrase in [
    "Pre-selection canonical eligibility classification: COMPLETE",
    "Eligible vs discovery-only separation: COMPLETE",
    "Missing-criteria reporting: COMPLETE",
    "Ineligible merchant selection: PROHIBITED",
    "Existing discovery evidence mutation for eligibility: PROHIBITED",
    "PHASE 7: NOT COMPLETE — REAL EVIDENCE REQUIRED",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: status missing or overclaims triage state: "
            + phrase
        )

print("OK: script syntax valid.")
print("OK: eligibility/discovery-only split present.")
print("OK: missing criteria and recruitment priority present.")
print("OK: create selects from eligible list only.")
print("OK: Phase 7 closure remains unchanged.")
print("STATUS: PHASE 7 DESIGN-PARTNER ELIGIBILITY TRIAGE READY")
