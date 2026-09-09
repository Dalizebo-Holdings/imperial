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
    VALIDATION / "decision/runtime.py",
    VALIDATION / "evidence/REAL_EVIDENCE_OPERATIONS.md",
    ROOT / "scripts/validation-evidence.py",
    ROOT / "scripts/evaluate-phase7-pmf.py",
    VALIDATION / "STATUS.md",
    VALIDATION / "IMPLEMENTATION_STATUS.md",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Phase 7 evidence operations file: {path}"
        )

for path in [
    VALIDATION / "evidence/runtime.py",
    VALIDATION / "evidence/store.py",
    VALIDATION / "decision/runtime.py",
    ROOT / "scripts/validation-evidence.py",
    ROOT / "scripts/evaluate-phase7-pmf.py",
]:
    py_compile.compile(
        str(path),
        doraise=True,
    )

runtime = importlib.import_module(
    "validation.evidence.runtime"
)
store_module = importlib.import_module(
    "validation.evidence.store"
)
decision = importlib.import_module(
    "validation.decision.runtime"
)

with TemporaryDirectory() as temp_dir:
    ledger_path = (
        Path(temp_dir)
        / "evidence-ledger.jsonl"
    )

    store = store_module.DurableEvidenceStore(
        ledger_path
    )
    initialized = store.initialize()

    if not initialized.exists():
        raise SystemExit(
            "ERROR: durable ledger was not initialized"
        )

    if (
        initialized.stat().st_mode
        & 0o777
    ) != 0o600:
        raise SystemExit(
            "ERROR: durable ledger permissions are not 0600"
        )

    payload = {
        "evidence_digest": "a" * 64,
        "metric_family": "discovery",
    }

    envelope = runtime.EvidenceEnvelope(
        envelope_id="real-evidence-001",
        evidence_type="GATE_PROOF",
        origin="REAL_MERCHANT",
        observed_at="2026-09-09T10:00:00+02:00",
        evidence_ref="evidence://phase7/discovery/001",
        source_system_ref="source://validation/discovery-registry",
        payload=payload,
        content_sha256=runtime.payload_sha256(
            payload
        ),
    )

    created = store.append(
        envelope
    )
    if created["created"] is not True:
        raise SystemExit(
            "ERROR: first durable append did not create evidence"
        )

    replay = store.append(
        envelope
    )
    if replay["created"] is not False:
        raise SystemExit(
            "ERROR: durable evidence replay was not idempotent"
        )

    loaded = store.load()
    if (
        loaded.count != 1
        or not loaded.verify_chain()
    ):
        raise SystemExit(
            "ERROR: durable ledger reconstruction/verification failed"
        )

    summary = store.summary()
    if (
        summary["count"] != 1
        or summary["decision_eligible_count"] != 1
        or summary["fixture_count"] != 0
        or not summary["chain_valid"]
    ):
        raise SystemExit(
            "ERROR: durable ledger summary failed"
        )

    export_path = (
        Path(temp_dir)
        / "verified-copy.jsonl"
    )
    store.export_verified(
        export_path
    )
    if (
        export_path.read_text(
            encoding="utf-8"
        )
        != ledger_path.read_text(
            encoding="utf-8"
        )
    ):
        raise SystemExit(
            "ERROR: verified evidence export mismatch"
        )

    # CLI ingest computes content_sha256 when omitted.
    fixture_input = (
        Path(temp_dir)
        / "fixture-envelope.json"
    )
    fixture_input.write_text(
        json.dumps({
            "envelope_id": "fixture-cli-001",
            "evidence_type": "GATE_PROOF",
            "origin": "TEST_FIXTURE",
            "observed_at": "2026-09-09T11:00:00+02:00",
            "evidence_ref": "evidence://test/cli/001",
            "source_system_ref": "source://validation/validator",
            "payload": {
                "evidence_digest": "b" * 64,
            },
        }),
        encoding="utf-8",
    )

    cli = subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "scripts/validation-evidence.py"
            ),
            "--ledger",
            str(
                ledger_path
            ),
            "ingest",
            str(
                fixture_input
            ),
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
        or "decision_eligible=false"
        not in cli.stdout
    ):
        raise SystemExit(
            "ERROR: evidence ingestion CLI failed fixture exclusion"
        )

    if store.summary()[
        "fixture_count"
    ] != 1:
        raise SystemExit(
            "ERROR: fixture evidence was not persisted/classified correctly"
        )

    # Public MVP evaluator exact canonical thresholds.
    snapshot_path = (
        Path(temp_dir)
        / "public-mvp.json"
    )
    snapshot_path.write_text(
        json.dumps({
            "snapshot_id": "real-shaped-public-mvp",
            "period_start": "2026-06-01T00:00:00+02:00",
            "period_end": "2026-09-01T00:00:00+02:00",
            "activated_organizations": 50,
            "monthly_transacting_organizations": 30,
            "active_three_consecutive_months": 20,
            "logo_start_count": 100,
            "logo_churned_count": 4,
            "first_transaction_eligible_organizations": 50,
            "first_transaction_within_24h": 15,
            "weekly_usage_eligible_organizations": 50,
            "weekly_active_organizations": 30,
            "payment_reconciliation_total": 200,
            "payment_reconciliation_matches": 199,
            "uptime_total_minutes": 100000,
            "uptime_available_minutes": 99500,
            "p95_core_api_latency_ms": 499,
            "checkout_api_p95_ms": 1499,
            "paying_customers": 10,
            "customer_references": 3,
            "critical_tenant_isolation_defects": 0,
            "backup_restore_test_passed": True,
            "evidence_refs": [
                "evidence://validator/public-mvp"
            ],
        }),
        encoding="utf-8",
    )

    public_eval = subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "scripts/evaluate-phase7-pmf.py"
            ),
            "--public-mvp-snapshot",
            str(
                snapshot_path
            ),
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
        public_eval.returncode != 0
        or '"state": "PASS"'
        not in public_eval.stdout
    ):
        raise SystemExit(
            "ERROR: Public MVP evaluator CLI failed"
        )

    # Closure must remain blocked with only incomplete/fixture proof set.
    manifest_path = (
        Path(temp_dir)
        / "proofs.json"
    )
    manifest_path.write_text(
        json.dumps({
            "proofs": [
                {
                    "label": "discovery",
                    "state": "PASS",
                    "evidence_digest": "a" * 64,
                    "evidence_ref": "evidence://phase7/discovery/001"
                }
            ]
        }),
        encoding="utf-8",
    )

    closure = subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "scripts/evaluate-phase7-pmf.py"
            ),
            "--ledger",
            str(
                ledger_path
            ),
            str(
                manifest_path
            ),
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
        closure.returncode != 0
        or '"state": "CONTINUE_VALIDATION"'
        not in closure.stdout
    ):
        raise SystemExit(
            "ERROR: incomplete real evidence incorrectly closed Phase 7"
        )

    required_flag = subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "scripts/evaluate-phase7-pmf.py"
            ),
            "--ledger",
            str(
                ledger_path
            ),
            "--require-complete",
            str(
                manifest_path
            ),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )

    if required_flag.returncode != 4:
        raise SystemExit(
            "ERROR: --require-complete did not fail closed"
        )

status = (
    VALIDATION / "STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "Durable evidence ledger: COMPLETE",
    "Actual real evidence imported: PENDING",
    "PHASE 7: NOT COMPLETE — REAL EVIDENCE REQUIRED",
    "Use the durable evidence CLI to collect/import real Phase 7 evidence",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Phase 7 status missing real-evidence operations or overclaims completion: "
            + phrase
        )

print("OK: Durable evidence store initialized with 0600 permissions.")
print("OK: Locked/fsync append + idempotent replay passed.")
print("OK: Ledger reconstruction/chain verification passed.")
print("OK: Verified ledger export passed.")
print("OK: Ingestion CLI computes digest and excludes TEST_FIXTURE.")
print("OK: Public MVP 90-day evaluator CLI passed.")
print("OK: Incomplete evidence remains CONTINUE_VALIDATION.")
print("OK: --require-complete fails closed until PHASE7_COMPLETE.")
print("STATUS: PHASE 7 REAL EVIDENCE OPERATIONS READY")
print("STATUS: PHASE 7 NOT COMPLETE — REAL EVIDENCE REQUIRED")
