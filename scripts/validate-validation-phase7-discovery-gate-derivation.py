#!/usr/bin/env python3
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

sys.path.insert(
    0,
    str(ROOT),
)

from validation.evidence.collection import envelope_from_input
from validation.evidence.derive import (
    EvidenceDerivationError,
    derive_discovery_gate,
    discovery_gate_proof_input,
)
from validation.evidence.store import DurableEvidenceStore


def main() -> int:
    required = [
        VALIDATION / "evidence/derive.py",
        VALIDATION / "evidence/DISCOVERY_GATE_DERIVATION.md",
        ROOT / "scripts/phase7-evidence-derive.py",
        VALIDATION / "STATUS.md",
        VALIDATION / "IMPLEMENTATION_STATUS.md",
    ]

    for path in required:
        if not path.exists():
            raise SystemExit(
                f"ERROR: missing discovery-gate derivation file: {path}"
            )

    with tempfile.TemporaryDirectory() as temp_dir:
        ledger_path = (
            Path(temp_dir)
            / "evidence-ledger.jsonl"
        )

        store = DurableEvidenceStore(
            ledger_path
        )
        store.initialize()

        empty = derive_discovery_gate(
            store
        )

        if (
            empty[
                "gate"
            ][
                "state"
            ]
            != "PENDING"
        ):
            raise SystemExit(
                "ERROR: empty durable ledger must derive PENDING"
            )

        if empty[
            "thresholds_waived"
        ] is not False:
            raise SystemExit(
                "ERROR: derivation may not waive thresholds"
            )

        try:
            discovery_gate_proof_input(
                derivation=empty
            )
        except EvidenceDerivationError:
            pass
        else:
            raise SystemExit(
                "ERROR: proof emission must fail while Discovery Gate is PENDING"
            )

        # TEST_FIXTURE evidence must remain excluded from the canonical registry.
        fixture = envelope_from_input({
            "envelope_id": "fixture-interview-001",
            "evidence_type": "DISCOVERY_INTERVIEW",
            "origin": "TEST_FIXTURE",
            "observed_at": "2026-09-09T09:00:00+02:00",
            "evidence_ref": "evidence://test/discovery/fixture-001",
            "source_system_ref": "source://validation/test-fixture",
            "payload": {
                "interview_id": "fixture-interview-001",
                "merchant_ref": "merchant://fixture/001",
                "merchant_segment": "Fixture Retail",
                "conducted_at": "2026-09-09T09:00:00+02:00",
                "products": ["COMMERCE", "POS"],
                "core_problem_material": True,
                "willingness_to_test": True,
                "structured_feedback_available": True,
                "evidence_ref": "evidence://test/discovery/domain-fixture-001",
                "metadata": {},
            },
        })

        store.append(
            fixture
        )

        after_fixture = derive_discovery_gate(
            store
        )

        if (
            after_fixture[
                "source_counts"
            ][
                "DISCOVERY_INTERVIEW"
            ]
            != 0
        ):
            raise SystemExit(
                "ERROR: TEST_FIXTURE interview leaked into Discovery derivation"
            )

        if (
            after_fixture[
                "gate"
            ][
                "interview_count"
            ]
            != 0
        ):
            raise SystemExit(
                "ERROR: fixture evidence changed canonical Discovery counts"
            )

    status = (
        VALIDATION
        / "STATUS.md"
    ).read_text(
        encoding="utf-8"
    )

    for phrase in [
        "Durable ledger -> canonical Discovery registry reconstruction: COMPLETE",
        "TEST_FIXTURE exclusion: COMPLETE",
        "PASS-only discovery GATE_PROOF emission: COMPLETE",
        "Discovery threshold waiver: PROHIBITED",
        "Actual discovery GATE_PROOF: PENDING REAL EVIDENCE",
        "PHASE 7: NOT COMPLETE — REAL EVIDENCE REQUIRED",
    ]:
        if phrase not in status:
            raise SystemExit(
                "ERROR: status missing or overclaims derivation state: "
                + phrase
            )

    print("OK: Empty real-evidence ledger derives Discovery=PENDING.")
    print("OK: TEST_FIXTURE discovery evidence is excluded.")
    print("OK: PENDING gate cannot emit a GATE_PROOF.")
    print("OK: Canonical thresholds are not waived.")
    print("OK: Phase 8 remains blocked by Phase 7 closure.")
    print("STATUS: PHASE 7 DISCOVERY GATE DERIVATION READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
