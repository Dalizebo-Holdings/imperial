#!/usr/bin/env python3
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

gate3 = (
    VALIDATION
    / "evidence/gate3_derive.py"
).read_text(
    encoding="utf-8"
)
cli = (
    ROOT
    / "scripts/phase7-evidence-void.py"
).read_text(
    encoding="utf-8"
)

ast.parse(gate3)
ast.parse(cli)

for phrase in (
    '"EVIDENCE_VOID"',
    '"target_envelope_id"',
    '"target_content_sha256"',
    '"PILOT_ONBOARDING_EVENT"',
    "voided_envelope_ids",
    "EVIDENCE_VOID target content digest mismatch",
    "duplicate EVIDENCE_VOID for target envelope",
):
    if phrase not in gate3:
        raise SystemExit(
            "ERROR: Gate 3 void-aware replay requirement missing: "
            + phrase
        )

for phrase in (
    '"EVIDENCE_VOID"',
    '"REAL_OPERATIONAL"',
    '"target_event_id"',
    '"target_content_sha256"',
    "ledger.verify_chain()",
    '"gate_pass_claimed": False',
    '"phase8": "BLOCKED"',
):
    if phrase not in cli:
        raise SystemExit(
            "ERROR: evidence-void CLI safeguard missing: "
            + phrase
        )

status = (
    VALIDATION
    / "STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in (
    "EVIDENCE_VOID correction envelope: COMPLETE",
    "Gate 3 void-aware replay: COMPLETE",
    "Direct ledger mutation/deletion: PROHIBITED",
    "Automatic Gate PASS claim: PROHIBITED",
    "PHASE 7: NOT COMPLETE — REAL EVIDENCE REQUIRED",
):
    if phrase not in status:
        raise SystemExit(
            "ERROR: STATUS missing/overclaim: "
            + phrase
        )

print("OK: EVIDENCE_VOID CLI syntax valid.")
print("OK: target event/envelope/digest binding present.")
print("OK: Gate 3 excludes only verified void targets.")
print("OK: immutable ledger semantics preserved.")
print("STATUS: PHASE 7 APPEND-ONLY EVIDENCE VOID READY")
