#!/usr/bin/env python3
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib
import json
import py_compile
import subprocess
import sys
import os

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

root_text = str(ROOT)
if root_text not in sys.path:
    sys.path.insert(
        0,
        root_text,
    )

required = [
    VALIDATION / "evidence/runtime.py",
    VALIDATION / "evidence/store.py",
    VALIDATION / "evidence/collection.py",
    VALIDATION / "evidence/REAL_EVIDENCE_COLLECTION.md",
    ROOT / "scripts/phase7-evidence-collect.py",
    VALIDATION / "STATUS.md",
    VALIDATION / "IMPLEMENTATION_STATUS.md",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Phase 7 collection file: {path}"
        )

for path in [
    VALIDATION / "evidence/runtime.py",
    VALIDATION / "evidence/store.py",
    VALIDATION / "evidence/collection.py",
    ROOT / "scripts/phase7-evidence-collect.py",
]:
    py_compile.compile(
        str(path),
        doraise=True,
    )

collection = importlib.import_module(
    "validation.evidence.collection"
)
store_module = importlib.import_module(
    "validation.evidence.store"
)

template_names = set(
    collection.templates()
)

expected_templates = {
    "discovery-interview",
    "design-partner-commitment",
    "pilot-status-transition",
    "pilot-onboarding",
    "pilot-onboarding-event",
    "pilot-metric-snapshot",
    "capacity-snapshot",
    "technical-attestation",
    "merchant-feedback",
    "support-evidence",
    "incident-evidence",
    "public-mvp-90d",
    "gate-proof",
}

if template_names != expected_templates:
    raise SystemExit(
        "ERROR: evidence template set mismatch"
    )

with TemporaryDirectory() as temp_dir:
    temp = Path(
        temp_dir
    )
    ledger = temp / "ledger.jsonl"
    inbox = temp / "inbox"
    template_library = temp / "templates"

    store = store_module.DurableEvidenceStore(
        ledger
    )
    store.initialize()

    result = collection.initialize_inbox(
        inbox,
        template_library=template_library,
    )

    if len(
        result["created_templates"]
    ) != len(
        expected_templates
    ):
        raise SystemExit(
            "ERROR: inbox templates were not created"
        )

    collection.create_record(
        template_type="discovery-interview",
        record_name="placeholder-interview",
        inbox=inbox,
        template_library=template_library,
    )

    # Placeholder templates must not pass preflight.
    initial = collection.preflight_inbox(
        store=store,
        inbox=inbox,
    )

    if initial["valid"] is not False:
        raise SystemExit(
            "ERROR: placeholder evidence passed preflight"
        )

    # Replace inbox with two valid test-fixture envelopes.
    for path in inbox.glob(
        "*.json"
    ):
        path.unlink()

    discovery = {
        "envelope_id": "fixture-discovery-001",
        "evidence_type": "DISCOVERY_INTERVIEW",
        "origin": "TEST_FIXTURE",
        "observed_at": "2026-09-09T10:00:00+02:00",
        "evidence_ref": "evidence://test/collection/discovery/001",
        "source_system_ref": "source://validation/validator",
        "payload": {
            "interview_id": "fixture-i-001",
            "merchant_ref": "merchant://fixture/001",
            "merchant_segment": "TEST_FIXTURE",
            "conducted_at": "2026-09-09T10:00:00+02:00",
            "products": [
                "POS"
            ],
            "core_problem_material": True,
            "willingness_to_test": True,
            "structured_feedback_available": True,
            "evidence_ref": "evidence://test/domain/discovery/001",
            "metadata": {
                "fixture": True
            },
        },
    }

    proof = {
        "envelope_id": "fixture-proof-001",
        "evidence_type": "GATE_PROOF",
        "origin": "TEST_FIXTURE",
        "observed_at": "2026-09-09T10:01:00+02:00",
        "evidence_ref": "evidence://test/collection/proof/001",
        "source_system_ref": "source://validation/validator",
        "payload": {
            "label": "discovery",
            "state": "PASS",
            "evidence_digest": "a" * 64,
        },
    }

    (inbox / "01-discovery.json").write_text(
        json.dumps(
            discovery
        ),
        encoding="utf-8",
    )
    (inbox / "02-proof.json").write_text(
        json.dumps(
            proof
        ),
        encoding="utf-8",
    )

    valid = collection.preflight_inbox(
        store=store,
        inbox=inbox,
    )

    if (
        valid["valid"] is not True
        or valid["ready"] != 2
    ):
        raise SystemExit(
            "ERROR: valid fixture inbox preflight failed"
        )

    ingested = collection.ingest_inbox(
        store=store,
        inbox=inbox,
    )

    if (
        ingested["created"] != 2
        or ingested["replayed"] != 0
    ):
        raise SystemExit(
            "ERROR: fixture batch ingestion failed"
        )

    replay = collection.ingest_inbox(
        store=store,
        inbox=inbox,
    )

    if (
        replay["created"] != 0
        or replay["replayed"] != 2
    ):
        raise SystemExit(
            "ERROR: batch replay was not idempotent"
        )

    progress = collection.progress(
        store
    )

    # Fixtures are persisted but excluded from decision-eligible progress.
    if (
        progress["ledger"]["fixture_count"] != 2
        or progress["ledger"]["decision_eligible_count"] != 0
        or progress["discovery_interviews"] != 0
        or progress["gate_proofs"]
    ):
        raise SystemExit(
            "ERROR: TEST_FIXTURE evidence contaminated real progress"
        )

    # CLI smoke.
    cli = subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "scripts/phase7-evidence-collect.py"
            ),
            "--ledger",
            str(
                ledger
            ),
            "--inbox",
            str(
                inbox
            ),
            "progress",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )

    if (
        cli.returncode != 0
        or '"phase7_complete_claimed": false'
        not in cli.stdout
    ):
        raise SystemExit(
            "ERROR: collection progress CLI failed"
        )

    # A fresh template generated via CLI must retain placeholder and be non-ingestible.
    template_cli = subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "scripts/phase7-evidence-collect.py"
            ),
            "template",
            "gate-proof",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )

    if (
        template_cli.returncode != 0
        or "__REPLACE__"
        not in template_cli.stdout
    ):
        raise SystemExit(
            "ERROR: evidence template CLI failed"
        )

status = (
    VALIDATION / "STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "Private evidence inbox: COMPLETE",
    "Batch preflight validation: COMPLETE",
    "Actual real evidence imported: IN PROGRESS",
    "PHASE 7: NOT COMPLETE — REAL EVIDENCE REQUIRED",
    "Initialize the empty private inbox",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Phase 7 status missing collection kit or overclaims real evidence: "
            + phrase
        )

print("OK: 13 private evidence templates installed.")
print("OK: Placeholder evidence fails closed.")
print("OK: Whole-inbox preflight passed valid fixtures.")
print("OK: Batch ingestion/replay idempotency passed.")
print("OK: TEST_FIXTURE evidence is excluded from real progress.")
print("OK: Progress/template CLI passed.")
print("STATUS: PHASE 7 REAL EVIDENCE COLLECTION KIT READY")
print("STATUS: PHASE 7 NOT COMPLETE — REAL EVIDENCE REQUIRED")
