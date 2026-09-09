#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "kernel/outbox/runtime.py"
MIGRATIONS = "\n".join(
    (ROOT / "kernel/migrations/sql" / name).read_text(encoding="utf-8")
    for name in ("0001_kernel_foundation.sql", "0004_phase8_outbox_delivery_hardening.sql")
)

spec = importlib.util.spec_from_file_location("kernel_outbox", RUNTIME)
if spec is None or spec.loader is None:
    raise SystemExit("ERROR: unable to load outbox worker runtime")
worker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = worker
spec.loader.exec_module(worker)

container = f"imperial-outbox-{uuid4().hex[:12]}"


def run(command: list[str], *, input_text: str | None = None) -> str:
    result = subprocess.run(
        command,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if result.returncode != 0:
        raise SystemExit(
            "ERROR: command failed: "
            + " ".join(command)
            + "\n"
            + result.stderr.strip()
        )
    return result.stdout.strip()


def psql(sql: str) -> str:
    return run(
        [
            "docker",
            "exec",
            "-i",
            container,
            "psql",
            "-U",
            "postgres",
            "-d",
            "postgres",
            "-v",
            "ON_ERROR_STOP=1",
            "-q",
            "-At",
            "-F",
            "|",
        ],
        input_text=sql,
    )


def execute_prepared(name: str, definition: str, values: str) -> str:
    return psql(f"PREPARE {name} AS {definition}; EXECUTE {name}({values});")


try:
    _ = run(
        [
            "docker",
            "run",
            "--rm",
            "--name",
            container,
            "-e",
            "POSTGRES_HOST_AUTH_METHOD=trust",
            "-d",
            "postgres:16-alpine",
        ]
    )
    deadline = time.monotonic() + 30
    while True:
        ready = subprocess.run(
            [
                "docker",
                "exec",
                container,
                "psql",
                "-U",
                "postgres",
                "-d",
                "postgres",
                "-Atqc",
                "SELECT 1",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if ready.returncode == 0 and ready.stdout.strip() == "1":
            break
        if time.monotonic() >= deadline:
            raise SystemExit("ERROR: PostgreSQL container did not become ready")
        time.sleep(0.5)

    setup = ""
    for statement in (
        "CREATE TABLE kernel.worker_validation_events (event_id text PRIMARY KEY, note text NOT NULL);",
        "INSERT INTO kernel.organizations (id, name) VALUES ('org-integration', 'validation');",
        "INSERT INTO kernel.outbox_events (event_id, event_type, event_version, organization_id, workspace_id, project_id, environment_id, resource_type, resource_id, occurred_at, correlation_id, actor_type, actor_id, payload) VALUES",
        "('evt-ack', 'order.created', '1', 'org-integration', 'ws-integration', 'proj-integration', 'env-integration', 'ORDER', 'order-ack', now(), 'corr-ack', 'SYSTEM', 'integration', '{\"kind\":\"ack\"}'),",
        "('evt-dead', 'order.created', '1', 'org-integration', 'ws-integration', 'proj-integration', 'env-integration', 'ORDER', 'order-dead', now(), 'corr-dead', 'SYSTEM', 'integration', '{\"kind\":\"dead\"}');",
        "INSERT INTO kernel.outbox_events (event_id, event_type, event_version, organization_id, workspace_id, project_id, environment_id, resource_type, resource_id, occurred_at, correlation_id, actor_type, actor_id, payload, max_attempts) VALUES ('evt-terminal', 'order.created', '1', 'org-integration', 'ws-integration', 'proj-integration', 'env-integration', 'ORDER', 'order-terminal', now(), 'corr-terminal', 'SYSTEM', 'integration', '{\"kind\":\"terminal\"}', 1);",
        "UPDATE kernel.outbox_events SET next_attempt_at = now() + interval '1 hour' WHERE event_id IN ('evt-dead', 'evt-terminal');",
    ):
        setup += f"{statement}\n"
    _ = psql(MIGRATIONS + "\n" + setup)

    first = execute_prepared(
        "claim_one",
        worker.CLAIM_SQL,
        "'worker-ack', 60, 'org-integration', 1",
    )
    if not first.startswith("evt-ack|"):
        raise SystemExit("ERROR: PostgreSQL claim did not return evt-ack: " + repr(first))
    if "ws-integration" not in first or "corr-ack" not in first:
        raise SystemExit("ERROR: PostgreSQL claim lost tenant or correlation context")

    second = execute_prepared(
        "claim_again",
        worker.CLAIM_SQL,
        "'worker-other', 60, 'org-integration', 1",
    )
    if second:
        raise SystemExit("ERROR: PostgreSQL lease allowed a double claim")

    acknowledged = execute_prepared(
        "ack_one",
        worker.ACK_SQL,
        "'evt-ack', 'org-integration', 'worker-ack'",
    )
    if acknowledged != "":
        raise SystemExit("ERROR: acknowledgement returned an unexpected row")
    if psql("SELECT outbox_status FROM kernel.outbox_events WHERE event_id = 'evt-ack';") != "PUBLISHED":
        raise SystemExit("ERROR: PostgreSQL publish acknowledgement was not durable")

    _ = psql("UPDATE kernel.outbox_events SET next_attempt_at = now() WHERE event_id = 'evt-dead';")
    claimed_dead = execute_prepared(
        "claim_dead",
        worker.CLAIM_SQL,
        "'worker-dead', 60, 'org-integration', 1",
    )
    if not claimed_dead.startswith("evt-dead|"):
        raise SystemExit("ERROR: PostgreSQL second event was not claimed")
    retry = execute_prepared(
        "fail_retry",
        worker.FAIL_SQL,
        "'evt-dead', 'org-integration', 'worker-dead', 'TEMPORARY_FAILURE'",
    )
    if retry != "":
        raise SystemExit("ERROR: retry transition returned an unexpected row")
    retry_state = psql(
        "SELECT outbox_status || '|' || (next_attempt_at > now())::text "
        + "FROM kernel.outbox_events WHERE event_id = 'evt-dead';"
    )
    if retry_state != "RETRY_PENDING|true":
        raise SystemExit("ERROR: PostgreSQL retry schedule was not persisted: " + repr(retry_state))

    _ = psql("UPDATE kernel.outbox_events SET next_attempt_at = now() WHERE event_id = 'evt-terminal';")
    claimed_terminal = execute_prepared(
        "claim_terminal",
        worker.CLAIM_SQL,
        "'worker-terminal', 60, 'org-integration', 1",
    )
    _ = execute_prepared(
        "fail_terminal",
        worker.FAIL_SQL,
        "'evt-terminal', 'org-integration', 'worker-terminal', 'FINAL_FAILURE'",
    )
    if not claimed_terminal.startswith("evt-terminal|"):
        raise SystemExit("ERROR: PostgreSQL terminal event was not claimed")
    if psql("SELECT outbox_status FROM kernel.outbox_events WHERE event_id = 'evt-terminal';") != "DEAD_LETTER":
        raise SystemExit("ERROR: PostgreSQL exhausted retry did not persist DEAD_LETTER")

    print("OK: PostgreSQL migrations applied in an ephemeral container")
    print("OK: PostgreSQL FOR UPDATE SKIP LOCKED claim is exclusive")
    print("OK: PostgreSQL tenant and correlation context is preserved")
    print("OK: PostgreSQL publish acknowledgement is durable")
    print("OK: PostgreSQL retry schedule is persisted")
    print("OK: PostgreSQL exhausted retry is terminal DEAD_LETTER")
    print("STATUS: PHASE 8 POSTGRESQL WORKER INTEGRATION READY")
finally:
    _ = subprocess.run(
        ["docker", "rm", "-f", container],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
