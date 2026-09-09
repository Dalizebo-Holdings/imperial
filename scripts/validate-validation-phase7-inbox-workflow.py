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

if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )

for path in [
    VALIDATION / "evidence/runtime.py",
    VALIDATION / "evidence/store.py",
    VALIDATION / "evidence/collection.py",
    ROOT / "scripts/phase7-evidence-collect.py",
]:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing evidence inbox workflow file: {path}"
        )
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

with TemporaryDirectory() as temp_dir:
    root = Path(temp_dir)
    inbox = root / "inbox"
    library = root / "templates"
    ledger = root / "ledger.jsonl"

    store = store_module.DurableEvidenceStore(
        ledger
    )
    store.initialize()

    initialized = collection.initialize_inbox(
        inbox,
        template_library=library,
    )

    if initialized["inbox_json_count"] != 0:
        raise SystemExit(
            "ERROR: init-inbox seeded placeholder files into active inbox"
        )

    if len(
        initialized["created_templates"]
    ) != 11:
        raise SystemExit(
            "ERROR: separate template library did not receive 11 templates"
        )

    workspace = collection.workspace_status(
        inbox=inbox,
        template_library=library,
    )

    if (
        workspace["inbox_count"] != 0
        or workspace["template_count"] != 11
    ):
        raise SystemExit(
            "ERROR: workspace separation failed"
        )

    empty = collection.preflight_inbox(
        store=store,
        inbox=inbox,
    )

    if (
        empty["valid"] is not True
        or empty["files"] != 0
        or empty["ready"] != 0
    ):
        raise SystemExit(
            "ERROR: empty active inbox should preflight successfully"
        )

    record = collection.create_record(
        template_type="discovery-interview",
        record_name="interview-001",
        inbox=inbox,
        template_library=library,
    )

    if not record.exists():
        raise SystemExit(
            "ERROR: new evidence record was not created"
        )

    if len(
        list(
            inbox.glob("*.json")
        )
    ) != 1:
        raise SystemExit(
            "ERROR: new command created unexpected active files"
        )

    placeholder = collection.preflight_inbox(
        store=store,
        inbox=inbox,
    )

    if placeholder["valid"] is not False:
        raise SystemExit(
            "ERROR: placeholder-bearing new record passed preflight"
        )

    # Fill the single active record with a valid fixture envelope.
    fixture = {
        "envelope_id": "fixture-inbox-workflow-001",
        "evidence_type": "DISCOVERY_INTERVIEW",
        "origin": "TEST_FIXTURE",
        "observed_at": "2026-09-09T10:00:00+02:00",
        "evidence_ref": "evidence://test/inbox-workflow/001",
        "source_system_ref": "source://validation/validator",
        "payload": {
            "interview_id": "fixture-interview-001",
            "merchant_ref": "merchant://fixture/001",
            "merchant_segment": "TEST_FIXTURE",
            "conducted_at": "2026-09-09T10:00:00+02:00",
            "products": ["POS"],
            "core_problem_material": True,
            "willingness_to_test": True,
            "structured_feedback_available": True,
            "evidence_ref": "evidence://test/domain/interview/001",
            "metadata": {"fixture": True},
        },
    }

    record.write_text(
        json.dumps(
            fixture,
            indent=2,
        ),
        encoding="utf-8",
    )

    valid = collection.preflight_inbox(
        store=store,
        inbox=inbox,
    )

    if (
        valid["valid"] is not True
        or valid["ready"] != 1
    ):
        raise SystemExit(
            "ERROR: single completed evidence record failed incremental preflight"
        )

    ingested = collection.ingest_inbox(
        store=store,
        inbox=inbox,
    )

    if ingested["created"] != 1:
        raise SystemExit(
            "ERROR: incremental evidence ingestion failed"
        )

    replay = collection.ingest_inbox(
        store=store,
        inbox=inbox,
    )

    if (
        replay["created"] != 0
        or replay["replayed"] != 1
    ):
        raise SystemExit(
            "ERROR: incremental replay is not idempotent"
        )

    try:
        collection.create_record(
            template_type="discovery-interview",
            record_name="interview-001",
            inbox=inbox,
            template_library=library,
        )
    except collection.EvidenceCollectionError:
        pass
    else:
        raise SystemExit(
            "ERROR: existing active evidence record was overwritten"
        )

    # CLI: clean fresh workspace should initialize empty inbox + 11 templates.
    cli_inbox = root / "cli-inbox"
    cli_library = root / "cli-templates"

    cli = subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "scripts/phase7-evidence-collect.py"
            ),
            "--ledger",
            str(ledger),
            "--inbox",
            str(cli_inbox),
            "--template-library",
            str(cli_library),
            "init-inbox",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )

    if cli.returncode != 0:
        raise SystemExit(
            "ERROR: init-inbox CLI failed"
        )

    cli_result = json.loads(
        cli.stdout
    )

    if (
        cli_result["inbox_json_count"] != 0
        or len(
            cli_result["created_templates"]
        ) != 11
    ):
        raise SystemExit(
            "ERROR: init-inbox CLI did not separate inbox/templates"
        )

    new_cli = subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "scripts/phase7-evidence-collect.py"
            ),
            "--ledger",
            str(ledger),
            "--inbox",
            str(cli_inbox),
            "--template-library",
            str(cli_library),
            "new",
            "merchant-feedback",
            "feedback-001",
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
        new_cli.returncode != 0
        or "PLACEHOLDERS_REQUIRE_REAL_EVIDENCE"
        not in new_cli.stdout
    ):
        raise SystemExit(
            "ERROR: new-record CLI failed"
        )

status = (
    VALIDATION / "STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "Empty active inbox initialization: COMPLETE",
    "Separate private template library: COMPLETE",
    "Incremental evidence collection: COMPLETE",
    "Actual real evidence imported: PENDING",
    "PHASE 7: NOT COMPLETE — REAL EVIDENCE REQUIRED",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: status missing inbox workflow or overclaims evidence: "
            + phrase
        )

print("OK: init-inbox creates an empty active inbox.")
print("OK: 11 placeholder templates are isolated in a private template library.")
print("OK: Empty inbox preflight passes.")
print("OK: `new` creates exactly one placeholder-bearing active record.")
print("OK: Placeholder active evidence still fails closed.")
print("OK: Single completed record preflight/ingestion/replay passed.")
print("OK: Existing record overwrite is rejected.")
print("STATUS: PHASE 7 EVIDENCE INBOX WORKFLOW READY")
print("STATUS: PHASE 7 NOT COMPLETE — REAL EVIDENCE REQUIRED")
