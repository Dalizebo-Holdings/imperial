#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
LOOP = ROOT / "orchestration/loop-os"
RUNTIME = LOOP / "runtime"

MODULES = {
    "job_model": RUNTIME / "job_model.py",
    "state_machine": RUNTIME / "state_machine.py",
    "queue_adapter": RUNTIME / "queue_adapter.py",
    "worker_contract": RUNTIME / "worker_contract.py",
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(f"ERROR: missing runtime file: {path}")

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

queue = queue_adapter.InMemoryQueueAdapter()

job = job_model.LoopJob(
    job_id="job-queue-validation-001",
    organization_id="org-validation",
    workflow_id="workflow-validation",
    job_type="success",
    max_attempts=2,
    timeout=30,
    idempotency_key="idem-queue-validation-001",
    correlation_id="corr-queue-validation-001",
    payload={"value": 4},
)

queued = queue.enqueue(
    job,
    available_at="2026-01-01T00:00:00+00:00",
)

if queued.status != "QUEUED":
    raise SystemExit("ERROR: CREATED job did not become QUEUED")

duplicate = job_model.LoopJob(
    job_id="job-queue-validation-duplicate",
    organization_id="org-validation",
    workflow_id="workflow-validation",
    job_type="success",
    max_attempts=2,
    timeout=30,
    idempotency_key="idem-queue-validation-001",
    correlation_id="corr-queue-validation-duplicate",
    payload={"value": 4},
)

try:
    queue.enqueue(
        duplicate,
        available_at="2026-01-01T00:00:00+00:00",
    )
except queue_adapter.DuplicateJobError:
    pass
else:
    raise SystemExit(
        "ERROR: duplicate idempotency submission was accepted"
    )

worker = worker_contract.Worker(queue)
executions = {"count": 0}


def success_handler(job):
    executions["count"] += 1
    return {"value": job.payload["value"] * 2}


worker.register_handler("success", success_handler)

denied = worker.run_one(
    authorization=worker_contract.ExecutionAuthorization(
        pillars_approved=True,
        kernel_authorized=False,
        authorization_ref="auth-denied",
    ),
    now="2026-01-01T00:00:00+00:00",
)

if denied is None:
    raise SystemExit("ERROR: queued job was not claimed")

if executions["count"] != 0:
    raise SystemExit(
        "ERROR: handler executed without Kernel authorization"
    )

if denied.job.status != "QUEUED":
    raise SystemExit(
        "ERROR: authorization-denied job changed execution state"
    )

approved = worker.run_one(
    authorization=worker_contract.ExecutionAuthorization(
        pillars_approved=True,
        kernel_authorized=True,
        authorization_ref="auth-approved",
    ),
    now="2026-01-01T00:00:01+00:00",
)

if approved is None:
    raise SystemExit("ERROR: approved queued job was not claimed")

if approved.job.status != "COMPLETED":
    raise SystemExit("ERROR: approved job did not complete")

if executions["count"] != 1:
    raise SystemExit("ERROR: handler execution count is incorrect")

if approved.job.result != {"value": 8}:
    raise SystemExit("ERROR: handler result was not persisted")

failure_job = job_model.LoopJob(
    job_id="job-queue-validation-002",
    organization_id="org-validation",
    workflow_id="workflow-validation",
    job_type="failure",
    max_attempts=2,
    timeout=30,
    idempotency_key="idem-queue-validation-002",
    correlation_id="corr-queue-validation-002",
    payload={},
)

queue.enqueue(
    failure_job,
    available_at="2026-01-01T00:00:02+00:00",
)


def failure_handler(job):
    raise RuntimeError("validation failure")


worker.register_handler("failure", failure_handler)

first_failure = worker.run_one(
    authorization=worker_contract.ExecutionAuthorization(
        pillars_approved=True,
        kernel_authorized=True,
        authorization_ref="auth-failure-1",
    ),
    now="2026-01-01T00:00:02+00:00",
)

if first_failure is None:
    raise SystemExit("ERROR: failure job was not claimed")

if first_failure.job.status != "RETRY_PENDING":
    raise SystemExit(
        "ERROR: first failure did not enter RETRY_PENDING"
    )

second_failure = worker.run_one(
    authorization=worker_contract.ExecutionAuthorization(
        pillars_approved=True,
        kernel_authorized=True,
        authorization_ref="auth-failure-2",
    ),
    now="2026-01-01T00:00:07+00:00",
)

if second_failure is None:
    raise SystemExit("ERROR: retry job was not claimed")

if second_failure.job.status != "DEAD_LETTERED":
    raise SystemExit(
        "ERROR: exhausted failure did not dead-letter"
    )

events = [
    event["event_type"]
    for event in first_failure.events + second_failure.events
]

for required in [
    "loop_os.job.started",
    "loop_os.job.retry_pending",
    "loop_os.job.dead_lettered",
]:
    if required not in events:
        raise SystemExit(
            f"ERROR: missing worker event: {required}"
        )

status = (LOOP / "IMPLEMENTATION_STATUS.md").read_text(
    encoding="utf-8"
)

for phrase in [
    "- [x] Queue adapter",
    "- [x] Worker execution contract",
    "- [ ] Loop audit adapter",
]:
    if phrase not in status:
        raise SystemExit(f"ERROR: Loop OS status missing: {phrase}")

print("OK: Queue adapter transitions CREATED -> QUEUED.")
print("OK: Duplicate idempotency submissions are rejected.")
print("OK: Worker blocks execution without Kernel authorization.")
print("OK: Authorized worker execution completes deterministically.")
print("OK: Failure enters bounded RETRY_PENDING state.")
print("OK: Exhausted retries become DEAD_LETTERED.")
print("OK: Worker emits structured lifecycle events.")
print("STATUS: LOOP OS QUEUE + WORKER P0 COMPLETE")
