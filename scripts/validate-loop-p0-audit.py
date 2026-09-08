#!/usr/bin/env python3

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import importlib.util
import py_compile
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
LOOP = ROOT / "orchestration/loop-os"
RUNTIME = LOOP / "runtime"

MODULES = {
    "job_model": RUNTIME / "job_model.py",
    "state_machine": RUNTIME / "state_machine.py",
    "queue_adapter": RUNTIME / "queue_adapter.py",
    "worker_contract": RUNTIME / "worker_contract.py",
    "audit_adapter": RUNTIME / "audit_adapter.py",
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(f"ERROR: missing Loop OS runtime file: {path}")

    py_compile.compile(str(path), doraise=True)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)

    if spec is None or spec.loader is None:
        raise SystemExit(f"ERROR: unable to load module: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


job_model = load_module("job_model", MODULES["job_model"])
state_machine = load_module(
    "state_machine",
    MODULES["state_machine"],
)
queue_adapter = load_module(
    "queue_adapter",
    MODULES["queue_adapter"],
)
worker_contract = load_module(
    "worker_contract",
    MODULES["worker_contract"],
)
audit_adapter = load_module(
    "audit_adapter",
    MODULES["audit_adapter"],
)

queue = queue_adapter.InMemoryQueueAdapter()

job = job_model.LoopJob(
    job_id="job-audit-validation-001",
    organization_id="org-validation",
    workflow_id="workflow-validation",
    job_type="audit-success",
    max_attempts=1,
    timeout=30,
    idempotency_key="idem-audit-validation-001",
    correlation_id="corr-audit-validation-001",
    payload={"value": 7},
)

queue.enqueue(
    job,
    available_at="2026-01-01T00:00:00+00:00",
)

worker = worker_contract.Worker(queue)


def handler(job):
    return {
        "ok": True,
        "api_key": "handler-result-secret",
    }


worker.register_handler("audit-success", handler)

result = worker.run_one(
    authorization=worker_contract.ExecutionAuthorization(
        pillars_approved=True,
        kernel_authorized=True,
        authorization_ref="auth-validation",
    ),
    now="2026-01-01T00:00:00+00:00",
)

if result is None:
    raise SystemExit("ERROR: validation worker returned no result")

if result.job.status != "COMPLETED":
    raise SystemExit("ERROR: validation worker did not complete")

if not result.events:
    raise SystemExit("ERROR: worker emitted no audit events")

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "loop-audit.jsonl"

    records = audit_adapter.persist_worker_result(
        path,
        worker_result=result,
        recorded_at="2026-01-01T00:00:01+00:00",
    )

    if len(records) != len(result.events):
        raise SystemExit(
            "ERROR: not all worker events were persisted"
        )

    verification = audit_adapter.verify_file(path)

    if not verification["valid"]:
        raise SystemExit(
            "ERROR: valid Loop OS audit chain failed: "
            + str(verification)
        )

    loaded = audit_adapter.read_records(path)

    if not loaded:
        raise SystemExit("ERROR: persisted audit file is empty")

    secret_event = {
        "event_type": "loop_os.job.started",
        "job_id": "job-secret-test",
        "correlation_id": "corr-secret-test",
        "attempt": 1,
        "authorization": "Bearer hidden",
        "metadata": {
            "api_key": "hidden-key",
            "safe": "retained",
        },
    }

    secret_record = audit_adapter.append_event(
        path,
        event=secret_event,
        recorded_at="2026-01-01T00:00:02+00:00",
    )

    if secret_record["event"]["authorization"] != "[REDACTED]":
        raise SystemExit(
            "ERROR: authorization secret was not redacted"
        )

    if (
        secret_record["event"]["metadata"]["api_key"]
        != "[REDACTED]"
    ):
        raise SystemExit(
            "ERROR: nested api_key was not redacted"
        )

    if secret_record["event"]["metadata"]["safe"] != "retained":
        raise SystemExit(
            "ERROR: safe metadata was incorrectly removed"
        )

    verification = audit_adapter.verify_file(path)

    if not verification["valid"]:
        raise SystemExit(
            "ERROR: extended audit chain failed verification"
        )

    tampered = deepcopy(
        audit_adapter.read_records(path)
    )
    tampered[0]["event"]["job_id"] = "tampered-job"

    tamper_result = audit_adapter.verify_records(tampered)

    if tamper_result["valid"]:
        raise SystemExit(
            "ERROR: tampered Loop OS audit record was accepted"
        )

status = (LOOP / "IMPLEMENTATION_STATUS.md").read_text(
    encoding="utf-8"
)

for phrase in [
    "- [x] Runtime job schema",
    "- [x] Deterministic state machine",
    "- [x] Bounded retry rules",
    "- [x] Timeout evaluation",
    "- [x] Dead-letter transition",
    "- [x] Idempotency fingerprint",
    "- [x] Queue adapter",
    "- [x] Worker execution contract",
    "- [x] Loop audit adapter",
    "P0 Status",
    "COMPLETE",
]:
    if phrase not in status:
        raise SystemExit(
            f"ERROR: Loop OS P0 status missing: {phrase}"
        )

print("OK: Worker lifecycle events persist to Loop OS audit.")
print("OK: Audit adapter recursively redacts sensitive values.")
print("OK: Append-only hash chaining passed.")
print("OK: Audit chain verification passed.")
print("OK: Tamper detection passed.")
print("OK: Loop OS P0 checklist is complete.")
print("STATUS: LOOP OS P0 COMPLETE")
