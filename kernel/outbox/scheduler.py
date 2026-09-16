from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from kernel.outbox.processor import ProcessingSummary


class SchedulerError(ValueError):
    pass


class PollingProcessor(Protocol):
    def run_once(self) -> ProcessingSummary: ...


@dataclass(frozen=True, slots=True)
class SchedulerSettings:
    poll_interval_seconds: float = 5
    max_cycles: int = 100

    def validate(self) -> None:
        if self.poll_interval_seconds <= 0:
            raise SchedulerError("poll_interval_seconds must be > 0")
        if self.max_cycles < 1:
            raise SchedulerError("max_cycles must be >= 1")


@dataclass(frozen=True, slots=True)
class SchedulerSummary:
    cycles: int
    idle_cycles: int
    claimed: int
    acknowledged: int
    failed: int


@dataclass(slots=True)
class SchedulerMetrics:
    cycles: int = 0
    idle_cycles: int = 0
    claimed: int = 0
    acknowledged: int = 0
    failed: int = 0

    def record(self, summary: SchedulerSummary) -> None:
        values = (
            summary.cycles,
            summary.idle_cycles,
            summary.claimed,
            summary.acknowledged,
            summary.failed,
        )
        if any(value < 0 for value in values):
            raise SchedulerError("scheduler summary values must be non-negative")
        self.cycles += summary.cycles
        self.idle_cycles += summary.idle_cycles
        self.claimed += summary.claimed
        self.acknowledged += summary.acknowledged
        self.failed += summary.failed

    def snapshot(self) -> dict[str, int]:
        return {
            "cycles": self.cycles,
            "idle_cycles": self.idle_cycles,
            "claimed": self.claimed,
            "acknowledged": self.acknowledged,
            "failed": self.failed,
        }


@dataclass(frozen=True, slots=True)
class OutboxScheduler:
    processor: PollingProcessor
    settings: SchedulerSettings
    metrics: SchedulerMetrics | None = None

    def run(
        self,
        *,
        sleep_fn: Callable[[float], None],
        stop_fn: Callable[[], bool] = lambda: False,
    ) -> SchedulerSummary:
        self.settings.validate()
        cycles = 0
        idle_cycles = 0
        claimed = 0
        acknowledged = 0
        failed = 0

        while cycles < self.settings.max_cycles:
            result = self.processor.run_once()
            cycles += 1
            claimed += result.claimed
            acknowledged += result.acknowledged
            failed += result.failed
            if self.metrics is not None:
                self.metrics.record(
                    SchedulerSummary(
                        cycles=1,
                        idle_cycles=int(result.claimed == 0),
                        claimed=result.claimed,
                        acknowledged=result.acknowledged,
                        failed=result.failed,
                    )
                )
            if result.claimed == 0:
                idle_cycles += 1
            if stop_fn():
                break
            if cycles < self.settings.max_cycles:
                sleep_fn(self.settings.poll_interval_seconds)

        return SchedulerSummary(
            cycles=cycles,
            idle_cycles=idle_cycles,
            claimed=claimed,
            acknowledged=acknowledged,
            failed=failed,
        )
