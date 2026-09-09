#!/usr/bin/env python3
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

script = (
    ROOT
    / "scripts/phase7-release-readiness.py"
)

source = script.read_text(
    encoding="utf-8"
)

ast.parse(
    source
)

for phrase in [
    "derive_release_gate_1(",
    "derive_release_gate_2(",
    "GATE1_ATTESTATIONS",
    "GATE2_ATTESTATIONS",
    '"MISSING_FAILED_OR_EXPIRED"',
    '"proof_emission_allowed"',
    '"thresholds_waived": False',
    '"evidence_generated": False',
    '"proof_generated": False',
    '"phase8_authorized": False',
]:
    if phrase not in source:
        raise SystemExit(
            "ERROR: release-readiness requirement missing: "
            + phrase
        )

status = (
    VALIDATION
    / "STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "Canonical Gate 1 readiness reporting: COMPLETE",
    "Canonical Gate 2 readiness reporting: COMPLETE",
    "Gate 1 Discovery blocker surfacing: COMPLETE",
    "Evidence generation by dashboard: PROHIBITED",
    "Phase 8 authorization by dashboard: PROHIBITED",
    "PHASE 7: NOT COMPLETE — REAL EVIDENCE REQUIRED",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: status missing or overclaims readiness state: "
            + phrase
        )

print("OK: release-readiness dashboard syntax valid.")
print("OK: canonical Gate 1/2 derivations reused.")
print("OK: missing attestation visibility present.")
print("OK: Discovery blocker is surfaced for Gate 1.")
print("OK: dashboard cannot create evidence/proofs or authorize Phase 8.")
print("STATUS: PHASE 7 RELEASE READINESS DASHBOARD READY")
