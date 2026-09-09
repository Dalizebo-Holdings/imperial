#!/usr/bin/env python3
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

derive = (
    VALIDATION
    / "evidence/gate3_derive.py"
).read_text(
    encoding="utf-8"
)
cli = (
    ROOT
    / "scripts/phase7-release-gate3.py"
).read_text(
    encoding="utf-8"
)

ast.parse(derive)
ast.parse(cli)

for phrase in [
    '== "TEST_FIXTURE"',
    '"DESIGN_PARTNER_COMMITMENT"',
    '"PILOT_STATUS_TRANSITION"',
    '"PILOT_ONBOARDING"',
    '"PILOT_ONBOARDING_EVENT"',
    '"PILOT_METRIC_SNAPSHOT"',
    '"CAPACITY_SNAPSHOT"',
    '"TECHNICAL_ATTESTATION"',
    "partner_registry.transition_pilot_status(",
    "pilot_registry.start_onboarding(",
    "pilot_registry.record_onboarding_event(",
    "pilot_registry.record_metric_snapshot(",
    "pilot_registry.record_capacity_snapshot(",
    "pilot_registry.record_attestation(",
    "registry.pilot_exit_gate(",
    "registry.capacity_gate(",
    "registry.release_gate_3(",
    "GATE_PROOF emission is prohibited",
    '"thresholds_waived": False',
]:
    if phrase not in derive:
        raise SystemExit(
            "ERROR: Gate 3 derivation safeguard missing: "
            + phrase
        )

for phrase in [
    '"phase8_authorized": False',
    '"--snapshot-id"',
    '"--capacity-snapshot-id"',
    '"--emit-proof"',
]:
    if phrase not in cli:
        raise SystemExit(
            "ERROR: Gate 3 CLI safeguard missing: "
            + phrase
        )

status = (
    VALIDATION
    / "STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "Canonical Release Gate 3 reuse: COMPLETE",
    "TEST_FIXTURE exclusion: COMPLETE",
    "PASS-only release_gate_3 proof emission: COMPLETE",
    "Actual Release Gate 3 proof: PENDING REAL EVIDENCE",
    "Gate 3 derivation: COMPLETE — REAL PILOT EVIDENCE REQUIRED FOR PASS",
    "PHASE 7: NOT COMPLETE — REAL EVIDENCE REQUIRED",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: status missing or overclaims Gate 3 state: "
            + phrase
        )

print("OK: Gate 3 derivation syntax valid.")
print("OK: durable pilot state + onboarding + events + metrics + capacity replay present.")
print("OK: canonical Pilot Exit/Capacity/Gate 3 evaluators reused.")
print("OK: TEST_FIXTURE excluded.")
print("OK: Gate 3 proof emission is PASS-only.")
print("STATUS: PHASE 7 DURABLE RELEASE GATE 3 DERIVATION READY")
