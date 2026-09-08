from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

try:
    from .job_model import LoopJob
except ImportError:
    from job_model import LoopJob


ALLOWED_TRANSITIONS = {
    "CREATED": {"QUEUED"},
    "QUEUED": {"RUNNING"},
    "RUNNING": {"COMPLETED", "FAILED"},
    "FAILED": {"RETRY_PENDING", "DEAD_LETTERED"},
    "RETRY_PENDING": {"RUNNING"},
    "COMPLETED": set(),
    "DEAD_LETTERED": set(),
}


class StateTransitionError(ValueError):
    pass


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def transition(
    job: LoopJob,
    target_status: str,
    *,
    now: str | None = None,
    result=None,
    error_code: str | None = None,
) -> LoopJob:
    job.validate()

    target = str(target_status).strip().upper()

    if target not in ALLOWED_TRANSITIONS:
        raise StateTransitionError(
            f"unknown target status: {target}"
        )

    if job.terminal:
        raise StateTransitionError(
            f"terminal job {job.job_id} may not transition from {job.status}"
        )

    allowed = ALLOWED_TRANSITIONS[job.status]

    if target not in allowed:
        raise StateTransitionError(
            f"invalid transition: {job.status} -> {target}"
        )

    timestamp = now or utc_now_iso()
    updated = replace(job)

    if target == "RUNNING":
        if updated.attempt >= updated.max_attempts:
            raise StateTransitionError(
                "cannot start another attempt; max_attempts exhausted"
            )

        updated.attempt += 1
        updated.started_at = timestamp
        updated.completed_at = None
        updated.error_code = None

    elif target == "COMPLETED":
        updated.completed_at = timestamp
        updated.result = result
        updated.error_code = None

    elif target == "FAILED":
        updated.completed_at = timestamp
        updated.error_code = (
            str(error_code).strip()
            if error_code is not None
            else "UNSPECIFIED_FAILURE"
        )

    elif target == "RETRY_PENDING":
        if updated.attempt >= updated.max_attempts:
            raise StateTransitionError(
                "retry prohibited; max_attempts exhausted"
            )

        updated.completed_at = None

    elif target == "DEAD_LETTERED":
        if updated.status != "FAILED":
            raise StateTransitionError(
                "only FAILED jobs may be dead-lettered"
            )

    updated.status = target
    updated.validate()
    return updated


def fail_or_retry(
    job: LoopJob,
    *,
    error_code: str,
    now: str | None = None,
) -> LoopJob:
    if job.status != "RUNNING":
        raise StateTransitionError(
            "fail_or_retry requires a RUNNING job"
        )

    failed = transition(
        job,
        "FAILED",
        now=now,
        error_code=error_code,
    )

    if failed.attempt >= failed.max_attempts:
        return transition(
            failed,
            "DEAD_LETTERED",
            now=now,
        )

    return transition(
        failed,
        "RETRY_PENDING",
        now=now,
    )


def exponential_backoff_seconds(
    attempt: int,
    *,
    base_seconds: int = 5,
    cap_seconds: int = 3600,
) -> int:
    if not isinstance(attempt, int) or attempt < 1:
        raise ValueError("attempt must be an integer >= 1")

    if not isinstance(base_seconds, int) or base_seconds < 1:
        raise ValueError("base_seconds must be an integer >= 1")

    if not isinstance(cap_seconds, int) or cap_seconds < 1:
        raise ValueError("cap_seconds must be an integer >= 1")

    delay = base_seconds * (2 ** (attempt - 1))
    return min(delay, cap_seconds)


def next_retry_at(
    job: LoopJob,
    *,
    now: str | None = None,
    base_seconds: int = 5,
    cap_seconds: int = 3600,
) -> str:
    job.validate()

    if job.status != "RETRY_PENDING":
        raise StateTransitionError(
            "next_retry_at requires RETRY_PENDING status"
        )

    current = (
        datetime.fromisoformat(now)
        if now is not None
        else datetime.now(timezone.utc)
    )

    delay = exponential_backoff_seconds(
        job.attempt,
        base_seconds=base_seconds,
        cap_seconds=cap_seconds,
    )

    return (current + timedelta(seconds=delay)).isoformat()


def is_timed_out(
    job: LoopJob,
    *,
    now: str | None = None,
) -> bool:
    job.validate()

    if job.status != "RUNNING":
        return False

    if job.started_at is None:
        raise StateTransitionError(
            "RUNNING job must have started_at"
        )

    started = datetime.fromisoformat(job.started_at)
    current = (
        datetime.fromisoformat(now)
        if now is not None
        else datetime.now(timezone.utc)
    )

    return current >= started + timedelta(seconds=job.timeout)
