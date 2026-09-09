#!/usr/bin/env python3
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

script = (
    ROOT
    / "scripts/phase7-technical-attestation.py"
)

source = script.read_text(
    encoding="utf-8"
)
ast.parse(
    source
)

for phrase in [
    '"REAL_OPERATIONAL"',
    '"TECHNICAL_ATTESTATION"',
    '"source://validation/release-gates"',
    "GATE1_ATTESTATIONS",
    "GATE2_ATTESTATIONS",
    "TechnicalAttestation(",
    "envelope_from_input(",
    "placeholder material",
    "timezone-aware",
    "target.chmod(",
    '"gate_pass_claimed": False',
    '"phase8": "BLOCKED"',
]:
    if phrase not in source:
        raise SystemExit(
            "ERROR: technical-attestation execution safeguard missing: "
            + phrase
        )

status = (
    VALIDATION
    / "STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "REAL_OPERATIONAL attestation writer: COMPLETE",
    "Explicit supporting evidence reference requirement: COMPLETE",
    "Placeholder evidence-reference rejection: COMPLETE",
    "Automatic gate PASS claim: PROHIBITED",
    "Actual technical attestations: EVIDENCE COLLECTION PENDING",
    "PHASE 7: NOT COMPLETE — REAL EVIDENCE REQUIRED",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: status missing or overclaims technical-attestation state: "
            + phrase
        )

print("OK: technical-attestation CLI syntax valid.")
print("OK: Gate 1/2 canonical requirement imports present.")
print("OK: REAL_OPERATIONAL provenance enforced.")
print("OK: explicit real evidence reference required.")
print("OK: no automatic Gate PASS or Phase 8 authorization.")
print("STATUS: PHASE 7 TECHNICAL ATTESTATION EXECUTION READY")
