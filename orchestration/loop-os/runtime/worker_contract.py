from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

try:
    from .job_model import LoopJob
    from .queue_adapter import InMemoryQueueAdapter
    from .state_machine import (
        fail_or_retry,
        next_retry_at,
        transition,
    )
except ImportError:
    from job_model import LoopJob
    from queue_adapter import InMemoryQueueAdapter
    from state_machine import (
        fail_or_retry,
        next_retry_at,
        transition,
    )


JobHandler = Callable[[LoopJob], Any]


class WorkerContractError(ValueError):
    pass


@dataclass(frozen=True)
class ExecutionAuthorization:
    pillars_approved: bool
    kernel_authorized: bool
    authorization_ref: str

    def validate(self) -> None:
        if not self.authorization_ref.strip():
            raise WorkerContractError(
                "authorization_ref must not be empty"
            )


@dataclass
class WorkerResult:
    job: LoopJob
    events: list[dict]


class Worker:
    def __init__(
        self,
        queue: InMemoryQueueAdapter,
    ) -> None:
        self.queue = queue
        self.handlers: dict[str, JobHandler] = {}

    def register_handler(
        self,
        job_type: str,
        handler: JobHandler,
    ) -> None:
        normalized = str(job_type).strip()

        if not normalized:
            raise WorkerContractError(
                "job_type must not be empty"
            )

        if not callable(handler):
            raise WorkerContractError(
                "handler must be callable"
            )

        self.handlers[normalized] = handler

    def execute_claimed(
        self,
        job: LoopJob,
        *,
        authorization: ExecutionAuthorization,
        now: str | None = None,
    ) -> WorkerResult:
        job.validate()
        authorization.validate()

        events = [
            {
                "event_type": "loop_os.job.claimed",
                "job_id": job.job_id,
                "correlation_id": job.correlation_id,
                "status": job.status,
            }
        ]

        if not (
            authorization.pillars_approved
            and authorization.kernel_authorized
        ):
            events.append(
                {
                    "event_type": "loop_os.job.authorization_denied",
                    "job_id": job.job_id,
                    "correlation_id": job.correlation_id,
                    "authorization_ref": authorization.authorization_ref,
                }
            )
            self.queue.release(job, available_at=now)
            return WorkerResult(job=job, events=events)

        handler = self.handlers.get(job.job_type)

        if handler is None:
            raise WorkerContractError(
                f"no handler registered for job_type={job.job_type}"
            )

        if job.status not in {"QUEUED", "RETRY_PENDING"}:
            raise WorkerContractError(
                f"job is not executable from status={job.status}"
            )

        running = transition(
            job,
            "RUNNING",
            now=now,
        )
        self.queue.update_claimed(running)

        events.append(
            {
                "event_type": "loop_os.job.started",
                "job_id": running.job_id,
                "correlation_id": running.correlation_id,
                "attempt": running.attempt,
                "authorization_ref": authorization.authorization_ref,
            }
        )

        try:
            result = handler(running)
        except Exception as exc:
            error_code = (
                "HANDLER_"
                + exc.__class__.__name__.upper()
            )

            failed_state = fail_or_retry(
                running,
                error_code=error_code,
                now=now,
            )

            self.queue.update_claimed(failed_state)

            if failed_state.status == "RETRY_PENDING":
                retry_at = next_retry_at(
                    failed_state,
                    now=now,
                )
                self.queue.enqueue_retry(
                    failed_state,
                    available_at=retry_at,
                )
                events.append(
                    {
                        "event_type": "loop_os.job.retry_pending",
                        "job_id": failed_state.job_id,
                        "correlation_id": failed_state.correlation_id,
                        "attempt": failed_state.attempt,
                        "error_code": failed_state.error_code,
                        "retry_at": retry_at,
                    }
                )
            else:
                self.queue.acknowledge(failed_state)
                events.append(
                    {
                        "event_type": "loop_os.job.dead_lettered",
                        "job_id": failed_state.job_id,
                        "correlation_id": failed_state.correlation_id,
                        "attempt": failed_state.attempt,
                        "error_code": failed_state.error_code,
                    }
                )

            return WorkerResult(
                job=failed_state,
                events=events,
            )

        completed = transition(
            running,
            "COMPLETED",
            now=now,
            result=result,
        )
        self.queue.update_claimed(completed)
        self.queue.acknowledge(completed)

        events.append(
            {
                "event_type": "loop_os.job.completed",
                "job_id": completed.job_id,
                "correlation_id": completed.correlation_id,
                "attempt": completed.attempt,
            }
        )

        return WorkerResult(
            job=completed,
            events=events,
        )

    def run_one(
        self,
        *,
        authorization: ExecutionAuthorization,
        now: str | None = None,
    ) -> WorkerResult | None:
        job = self.queue.claim_ready(now=now)

        if job is None:
            return None

        return self.execute_claimed(
            job,
            authorization=authorization,
            now=now,
        )
