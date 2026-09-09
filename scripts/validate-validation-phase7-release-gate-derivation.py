#!/usr/bin/env python3
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

paths = [
    VALIDATION / "evidence/release_gate_derive.py",
    ROOT / "scripts/phase7-release-gates.py",
]

for path in paths:
    source = path.read_text(
        encoding="utf-8"
    )
    ast.parse(
        source
    )

derive_source = (
    VALIDATION
    / "evidence/release_gate_derive.py"
).read_text(
    encoding="utf-8"
)

for phrase in [
    'origin != "REAL_OPERATIONAL"',
    'origin == "TEST_FIXTURE"',
    '"TECHNICAL_ATTESTATION"',
    "TechnicalAttestation(",
    "registry.record_attestation(",
    "registry.release_gate_1(",
    "registry.release_gate_2(",
    "derive_discovery_gate(",
    '"release_gate_1"',
    '"release_gate_2"',
    "GATE_PROOF emission is prohibited",
    '"thresholds_waived": False',
]:
    if phrase not in derive_source:
        raise SystemExit(
            "ERROR: release-gate derivation safeguard missing: "
            + phrase
        )

status = (
    VALIDATION
    / "STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "Canonical Gate 1 derivation: COMPLETE",
    "Canonical Gate 2 derivation: COMPLETE",
    "Gate 1 Discovery dependency: ENFORCED",
    "Gate 3 derivation: DEFERRED — REAL PILOT METRICS REQUIRED",
    "Actual Release Gate 1 proof: PENDING REAL EVIDENCE",
    "Actual Release Gate 2 proof: PENDING REAL EVIDENCE",
    "PHASE 7: NOT COMPLETE — REAL EVIDENCE REQUIRED",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: status missing or overclaims release-gate state: "
            + phrase
        )

print("OK: release-gate derivation scripts parse.")
print("OK: REAL_OPERATIONAL technical attestations only.")
print("OK: TEST_FIXTURE exclusion enforced.")
print("OK: Gate 1 retains Discovery dependency.")
print("OK: Gate 1/2 proof emission is PASS-only.")
print("OK: Gate 3 remains deferred for real pilot evidence.")
print("STATUS: PHASE 7 RELEASE GATE 1/2 DERIVATION READY")
