#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
LOOP = ROOT / "orchestration/loop-os"
RUNTIME = LOOP / "runtime"

JOB_MODEL = RUNTIME / "job_model.py"
STATE_MACHINE = RUNTIME / "state_machine.py"

for path in [JOB_MODEL, STATE_MACHINE]:
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


job_model = load_module("job_model", JOB_MODEL)
state_machine = load_module("state_machine", STATE_MACHINE)

job = job_model.LoopJob(
    job_id="job-validation-001",
    organization_id="org-validation",
    workflow_id="workflow-validation",
    job_type="validation",
    max_attempts=2,
    timeout=60,
    idempotency_key="idem-validation",
    correlation_id="corr-validation",
    payload={"action": "validate"},
)

job.validate()

fingerprint_one = job.fingerprint()
fingerprint_two = job.fingerprint()

if fingerprint_one != fingerprint_two:
    raise SystemExit("ERROR: idempotency fingerprint is not deterministic")

queued = state_machine.transition(
    job,
    "QUEUED",
    now="2026-01-01T00:00:00+00:00",
)

running = state_machine.transition(
    queued,
    "RUNNING",
    now="2026-01-01T00:00:01+00:00",
)

if running.attempt != 1:
    raise SystemExit("ERROR: RUNNING did not increment attempt")

if not state_machine.is_timed_out(
    running,
    now="2026-01-01T00:01:01+00:00",
):
    raise SystemExit("ERROR: timeout boundary was not detected")

retry_pending = state_machine.fail_or_retry(
    running,
    error_code="VALIDATION_FAILURE",
    now="2026-01-01T00:01:01+00:00",
)

if retry_pending.status != "RETRY_PENDING":
    raise SystemExit("ERROR: retryable failure did not enter RETRY_PENDING")

retry_at = state_machine.next_retry_at(
    retry_pending,
    now="2026-01-01T00:01:01+00:00",
    base_seconds=5,
)

if retry_at != "2026-01-01T00:01:06+00:00":
    raise SystemExit(
        "ERROR: deterministic retry backoff is incorrect: " + retry_at
    )

running_two = state_machine.transition(
    retry_pending,
    "RUNNING",
    now="2026-01-01T00:01:06+00:00",
)

if running_two.attempt != 2:
    raise SystemExit("ERROR: second RUNNING attempt did not increment")

dead = state_machine.fail_or_retry(
    running_two,
    error_code="SECOND_FAILURE",
    now="2026-01-01T00:01:07+00:00",
)

if dead.status != "DEAD_LETTERED":
    raise SystemExit("ERROR: exhausted retry did not dead-letter")

try:
    state_machine.transition(
        dead,
        "RUNNING",
        now="2026-01-01T00:01:08+00:00",
    )
except state_machine.StateTransitionError:
    pass
else:
    raise SystemExit("ERROR: terminal job was allowed to transition")

success_job = job_model.LoopJob(
    job_id="job-validation-002",
    organization_id="org-validation",
    workflow_id="workflow-validation",
    job_type="validation",
    max_attempts=1,
    timeout=60,
    idempotency_key="idem-validation-success",
    correlation_id="corr-validation-success",
    payload={"action": "validate-success"},
)

success_job = state_machine.transition(
    success_job,
    "QUEUED",
    now="2026-01-01T00:00:00+00:00",
)

success_job = state_machine.transition(
    success_job,
    "RUNNING",
    now="2026-01-01T00:00:01+00:00",
)

success_job = state_machine.transition(
    success_job,
    "COMPLETED",
    now="2026-01-01T00:00:02+00:00",
    result={"ok": True},
)

if success_job.status != "COMPLETED":
    raise SystemExit("ERROR: success lifecycle did not complete")

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
]:
    if phrase not in status:
        raise SystemExit(f"ERROR: Loop OS status missing: {phrase}")

print("OK: Loop OS job schema validation passed.")
print("OK: Idempotency fingerprint is deterministic.")
print("OK: Lifecycle CREATED -> QUEUED -> RUNNING -> COMPLETED passed.")
print("OK: Retry path is bounded and deterministic.")
print("OK: Exhausted retries transition to DEAD_LETTERED.")
print("OK: Terminal jobs reject further transitions.")
print("OK: Timeout evaluation passed.")
print("STATUS: LOOP OS RUNTIME + STATE MACHINE P0 COMPLETE")
