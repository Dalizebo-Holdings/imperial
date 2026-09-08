from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Iterable

try:
    from .job_model import LoopJob
    from .state_machine import transition
except ImportError:
    from job_model import LoopJob
    from state_machine import transition


class QueueAdapterError(ValueError):
    pass


class DuplicateJobError(QueueAdapterError):
    pass


class QueueStateError(QueueAdapterError):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _timestamp(value: str) -> float:
    return datetime.fromisoformat(value).timestamp()


@dataclass
class QueueEntry:
    job: LoopJob
    available_at: str
    sequence: int
    claimed: bool = False

    def validate(self) -> None:
        self.job.validate()
        datetime.fromisoformat(self.available_at)

        if self.sequence < 1:
            raise QueueAdapterError("sequence must be >= 1")


class InMemoryQueueAdapter:
    def __init__(self) -> None:
        self._entries: dict[str, QueueEntry] = {}
        self._idempotency: dict[tuple[str, str], str] = {}
        self._sequence = 0

    def _idempotency_identity(self, job: LoopJob) -> tuple[str, str]:
        job.validate()
        return (job.organization_id, job.idempotency_key)

    def _assert_duplicate_safe(self, job: LoopJob) -> None:
        identity = self._idempotency_identity(job)
        existing_job_id = self._idempotency.get(identity)

        if existing_job_id is None:
            return

        existing = self._entries.get(existing_job_id)

        if existing is None:
            return

        if existing.job.fingerprint() == job.fingerprint():
            raise DuplicateJobError(
                f"duplicate idempotent job: {existing_job_id}"
            )

        raise DuplicateJobError(
            "idempotency key reused with different job material"
        )

    def enqueue(
        self,
        job: LoopJob,
        *,
        available_at: str | None = None,
    ) -> LoopJob:
        job.validate()

        if job.status != "CREATED":
            raise QueueStateError(
                "enqueue requires CREATED status"
            )

        self._assert_duplicate_safe(job)

        timestamp = available_at or job.scheduled_at or _now_iso()
        datetime.fromisoformat(timestamp)

        queued = transition(
            job,
            "QUEUED",
            now=timestamp,
        )

        self._sequence += 1
        entry = QueueEntry(
            job=queued,
            available_at=timestamp,
            sequence=self._sequence,
        )
        entry.validate()

        self._entries[queued.job_id] = entry
        self._idempotency[
            self._idempotency_identity(queued)
        ] = queued.job_id

        return replace(queued)

    def enqueue_retry(
        self,
        job: LoopJob,
        *,
        available_at: str,
    ) -> LoopJob:
        job.validate()

        if job.status != "RETRY_PENDING":
            raise QueueStateError(
                "enqueue_retry requires RETRY_PENDING status"
            )

        datetime.fromisoformat(available_at)

        existing = self._entries.get(job.job_id)

        if existing is None:
            identity = self._idempotency_identity(job)
            prior = self._idempotency.get(identity)

            if prior is not None and prior != job.job_id:
                raise DuplicateJobError(
                    f"idempotency identity belongs to {prior}"
                )

            self._sequence += 1
            sequence = self._sequence
        else:
            sequence = existing.sequence

        entry = QueueEntry(
            job=replace(job),
            available_at=available_at,
            sequence=sequence,
            claimed=False,
        )
        entry.validate()

        self._entries[job.job_id] = entry
        self._idempotency[
            self._idempotency_identity(job)
        ] = job.job_id

        return replace(job)

    def claim_ready(
        self,
        *,
        now: str | None = None,
    ) -> LoopJob | None:
        current = now or _now_iso()
        current_ts = _timestamp(current)

        candidates = [
            entry
            for entry in self._entries.values()
            if not entry.claimed
            and entry.job.status in {"QUEUED", "RETRY_PENDING"}
            and _timestamp(entry.available_at) <= current_ts
        ]

        if not candidates:
            return None

        candidates.sort(
            key=lambda entry: (
                _timestamp(entry.available_at),
                entry.sequence,
            )
        )

        selected = candidates[0]
        selected.claimed = True
        return replace(selected.job)

    def acknowledge(self, job: LoopJob) -> None:
        job.validate()

        entry = self._entries.get(job.job_id)
        if entry is None:
            raise QueueAdapterError(
                f"unknown queued job: {job.job_id}"
            )

        if job.status not in {"COMPLETED", "DEAD_LETTERED"}:
            raise QueueStateError(
                "acknowledge requires terminal status"
            )

        entry.job = replace(job)
        entry.claimed = False

    def release(
        self,
        job: LoopJob,
        *,
        available_at: str | None = None,
    ) -> None:
        job.validate()

        entry = self._entries.get(job.job_id)
        if entry is None:
            raise QueueAdapterError(
                f"unknown queued job: {job.job_id}"
            )

        if job.status not in {"QUEUED", "RETRY_PENDING"}:
            raise QueueStateError(
                "release requires QUEUED or RETRY_PENDING status"
            )

        entry.job = replace(job)
        entry.available_at = available_at or _now_iso()
        datetime.fromisoformat(entry.available_at)
        entry.claimed = False

    def update_claimed(self, job: LoopJob) -> None:
        job.validate()

        entry = self._entries.get(job.job_id)
        if entry is None:
            raise QueueAdapterError(
                f"unknown queued job: {job.job_id}"
            )

        if not entry.claimed:
            raise QueueStateError(
                "update_claimed requires an active claim"
            )

        entry.job = replace(job)

    def get(self, job_id: str) -> LoopJob | None:
        entry = self._entries.get(job_id)
        return replace(entry.job) if entry else None

    def list_entries(self) -> list[QueueEntry]:
        return [
            QueueEntry(
                job=replace(entry.job),
                available_at=entry.available_at,
                sequence=entry.sequence,
                claimed=entry.claimed,
            )
            for entry in sorted(
                self._entries.values(),
                key=lambda item: item.sequence,
            )
        ]
