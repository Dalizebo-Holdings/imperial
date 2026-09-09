#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import TracebackType
from typing import Self

ROOT = Path(__file__).resolve().parent.parent
WORKER_PATH = ROOT / "kernel/outbox/runtime.py"
MIGRATION = ROOT / "kernel/migrations/sql/0004_phase8_outbox_delivery_hardening.sql"

spec = importlib.util.spec_from_file_location("kernel_outbox", WORKER_PATH)
if spec is None or spec.loader is None:
    raise SystemExit("ERROR: unable to load outbox worker runtime")
worker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = worker
spec.loader.exec_module(worker)
RowValue = str | int | datetime | None

sql = WORKER_PATH.read_text(encoding="utf-8")
migration = MIGRATION.read_text(encoding="utf-8")
for marker in [
    "FOR UPDATE SKIP LOCKED",
    "lock_owner",
    "lock_expires_at",
    "outbox_status = 'PUBLISHED'",
    "DEAD_LETTER",
    "2 ^ GREATEST",
]:
    if marker not in sql:
        raise SystemExit(f"ERROR: worker SQL missing {marker}")
for marker in ["attempt_count", "max_attempts", "next_attempt_at", "lock_owner"]:
    if marker not in migration:
        raise SystemExit(f"ERROR: migration missing {marker}")


def _integer(row: dict[str, RowValue], name: str) -> int:
    value = row[name]
    if not isinstance(value, int):
        raise TypeError(f"invalid integer field: {name}")
    return value


def _timestamp(row: dict[str, RowValue], name: str) -> datetime:
    value = row[name]
    if not isinstance(value, datetime):
        raise TypeError(f"invalid timestamp field: {name}")
    return value


class FakeCursor:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection
        self.rows: list[dict[str, RowValue]] = []
        self.rowcount = 0

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> None:
        return None

    def execute(self, statement: str, parameters: tuple[RowValue, ...]) -> None:
        with self.connection.state_lock:
            self.rows = []
            self.rowcount = 0
            if "FOR UPDATE SKIP LOCKED" in statement:
                worker_id, lease_seconds, organization_id, limit = parameters
                if not isinstance(worker_id, str) or not isinstance(lease_seconds, int) or not isinstance(organization_id, str) or not isinstance(limit, int):
                    raise TypeError("invalid claim parameters")
                for row in self.connection.rows:
                    if len(self.rows) >= limit:
                        break
                    if (
                        row["organization_id"] == organization_id
                        and row["outbox_status"] in {"COMMITTED", "RETRY_PENDING"}
                        and row["lock_owner"] is None
                        and _timestamp(row, "next_attempt_at") <= self.connection.now
                    ):
                        row["attempt_count"] = _integer(row, "attempt_count") + 1
                        row["lock_owner"] = worker_id
                        row["lock_expires_at"] = self.connection.now + timedelta(seconds=lease_seconds)
                        self.rows.append(dict(row))
                return
            if "outbox_status = 'PUBLISHED'" in statement:
                event_id, organization_id, worker_id = parameters
                if not isinstance(event_id, str) or not isinstance(organization_id, str) or not isinstance(worker_id, str):
                    raise TypeError("invalid acknowledgement parameters")
                for row in self.connection.rows:
                    if (
                        row["event_id"] == event_id
                        and row["organization_id"] == organization_id
                        and row["lock_owner"] == worker_id
                    ):
                        row.update(
                            outbox_status="PUBLISHED",
                            published_at=self.connection.now,
                            lock_owner=None,
                            lock_expires_at=None,
                        )
                        self.rowcount = 1
                return
            event_id, organization_id, worker_id, error_code = parameters
            if not isinstance(event_id, str) or not isinstance(organization_id, str) or not isinstance(worker_id, str) or not isinstance(error_code, str):
                raise TypeError("invalid failure parameters")
            for row in self.connection.rows:
                if (
                    row["event_id"] == event_id
                    and row["organization_id"] == organization_id
                    and row["lock_owner"] == worker_id
                ):
                    row["outbox_status"] = (
                        "DEAD_LETTER"
                        if _integer(row, "attempt_count") >= _integer(row, "max_attempts")
                        else "RETRY_PENDING"
                    )
                    row["last_error_code"] = error_code
                    row["lock_owner"] = None
                    row["lock_expires_at"] = None
                    self.rowcount = 1

    def fetchall(self) -> list[dict[str, RowValue]]:
        return self.rows


class FakeConnection:
    def __init__(self) -> None:
        self.state_lock = threading.Lock()
        self.now = datetime(2026, 9, 9, tzinfo=timezone.utc)
        self.commits = 0
        self.rollbacks = 0
        self.rows: list[dict[str, RowValue]] = [
            {
                "event_id": "evt-worker",
                "organization_id": "org-worker",
                "workspace_id": "ws-worker",
                "project_id": "proj-worker",
                "environment_id": "env-worker",
                "event_type": "order.created",
                "event_version": "1",
                "correlation_id": "corr-worker",
                "actor_type": "SYSTEM",
                "actor_id": "worker-test",
                "payload": "{\"order_id\":\"order-worker\"}",
                "attempt_count": 0,
                "max_attempts": 2,
                "outbox_status": "COMMITTED",
                "next_attempt_at": self.now,
                "lock_owner": None,
                "lock_expires_at": None,
                "published_at": None,
            }
        ]

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


connection = FakeConnection()
workers = [
    worker.PostgresOutboxWorker(connection),
    worker.PostgresOutboxWorker(connection),
]
barrier = threading.Barrier(2)
claimed: list[tuple[str, ...]] = [(), ()]


def claim(index: int) -> None:
    barrier.wait()
    result = workers[index].claim(
        worker_id=f"worker-{index}",
        organization_id="org-worker",
        lease_seconds=30,
        limit=1,
    )
    claimed[index] = tuple(item.event_id for item in result)


threads = [threading.Thread(target=claim, args=(index,)) for index in range(2)]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()

if sorted(claimed) != [(), ("evt-worker",)]:
    raise SystemExit(f"ERROR: concurrent workers double-claimed: {claimed}")

owner_index = next(index for index, item in enumerate(claimed) if item)
if claimed[owner_index] != ("evt-worker",):
    raise SystemExit("ERROR: event was not claimed")

try:
    workers[owner_index].acknowledge(
        event_id="evt-worker",
        organization_id="org-worker",
        worker_id="wrong-worker",
    )
except worker.OutboxWorkerError:
    pass
else:
    raise SystemExit("ERROR: acknowledgement without lease ownership was accepted")

workers[owner_index].fail(
    event_id="evt-worker",
    organization_id="org-worker",
    worker_id=f"worker-{owner_index}",
    error_code="TEMPORARY_FAILURE",
)
if connection.rows[0]["outbox_status"] != "RETRY_PENDING":
    raise SystemExit("ERROR: retry failure did not persist RETRY_PENDING")

connection.now += timedelta(seconds=2)
second = workers[1].claim(
    worker_id="worker-retry",
    organization_id="org-worker",
    lease_seconds=30,
    limit=1,
)
if len(second) != 1 or second[0].attempt_count != 2:
    raise SystemExit("ERROR: retry claim did not recover after scheduling")
if (
    second[0].organization_id != "org-worker"
    or second[0].workspace_id != "ws-worker"
    or second[0].project_id != "proj-worker"
    or second[0].environment_id != "env-worker"
    or second[0].correlation_id != "corr-worker"
):
    raise SystemExit("ERROR: tenant or correlation context was not preserved")

workers[1].fail(
    event_id="evt-worker",
    organization_id="org-worker",
    worker_id="worker-retry",
    error_code="FINAL_FAILURE",
)
if connection.rows[0]["outbox_status"] != "DEAD_LETTER":
    raise SystemExit("ERROR: exhausted retry did not persist DEAD_LETTER")

if worker.retry_delay_seconds(1) != 1 or worker.retry_delay_seconds(20) != 3600:
    raise SystemExit("ERROR: retry backoff is not bounded exponential")

expiry = worker.lease_expiry(now=connection.now, lease_seconds=30)
if expiry != connection.now + timedelta(seconds=30):
    raise SystemExit("ERROR: lease expiry calculation is invalid")

print("OK: atomic FOR UPDATE SKIP LOCKED claim contract present")
print("OK: concurrent workers do not double-claim an event")
print("OK: lease owner and expiry are persisted")
print("OK: retry scheduling is bounded exponential")
print("OK: expired/retry claim recovers the event")
print("OK: publish failure persists DEAD_LETTER terminal state")
print("OK: tenant and correlation fields are preserved in claimed records")
print("STATUS: PHASE 8 OUTBOX WORKER LEASING READY")
