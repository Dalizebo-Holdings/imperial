#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kernel.outbox.processor import ProcessingSummary
from kernel.outbox.scheduler import (
    OutboxScheduler,
    SchedulerError,
    SchedulerMetrics,
    SchedulerSettings,
)


class FakeProcessor:
    def __init__(self, summaries: list[ProcessingSummary]) -> None:
        self.summaries = iter(summaries)
        self.calls = 0

    def run_once(self) -> ProcessingSummary:
        self.calls += 1
        return next(self.summaries)


sleep_calls: list[float] = []
processor = FakeProcessor(
    [
        ProcessingSummary(claimed=2, acknowledged=1, failed=1),
        ProcessingSummary(claimed=0, acknowledged=0, failed=0),
        ProcessingSummary(claimed=0, acknowledged=0, failed=0),
    ]
)
scheduler_metrics = SchedulerMetrics()
scheduler = OutboxScheduler(
    processor=processor,
    settings=SchedulerSettings(poll_interval_seconds=5, max_cycles=3),
    metrics=scheduler_metrics,
)
summary = scheduler.run(sleep_fn=sleep_calls.append)
if summary.cycles != 3 or summary.claimed != 2 or summary.acknowledged != 1 or summary.failed != 1:
    raise SystemExit(f"ERROR: scheduler summary is invalid: {summary}")
if summary.idle_cycles != 2 or processor.calls != 3:
    raise SystemExit("ERROR: scheduler did not execute its bounded cycle budget")
if sleep_calls != [5, 5]:
    raise SystemExit(f"ERROR: scheduler polling interval was not applied: {sleep_calls}")

zero = OutboxScheduler(
    processor=FakeProcessor([ProcessingSummary(claimed=0, acknowledged=0, failed=0)]),
    settings=SchedulerSettings(poll_interval_seconds=1, max_cycles=1),
).run(sleep_fn=lambda _: None)
if zero.cycles != 1 or zero.idle_cycles != 1:
    raise SystemExit("ERROR: empty poll was not recorded as idle")

stopped = OutboxScheduler(
    processor=FakeProcessor(
        [
            ProcessingSummary(claimed=1, acknowledged=1, failed=0),
            ProcessingSummary(claimed=1, acknowledged=1, failed=0),
        ]
    ),
    settings=SchedulerSettings(poll_interval_seconds=1, max_cycles=5),
).run(sleep_fn=lambda _: None, stop_fn=lambda: True)
if stopped.cycles != 1 or stopped.acknowledged != 1:
    raise SystemExit("ERROR: scheduler did not honor a graceful stop request")

metrics = SchedulerMetrics()
metrics.record(summary)
metrics.record(zero)
metrics_snapshot = metrics.snapshot()
if metrics_snapshot != {
    "cycles": 4,
    "idle_cycles": 3,
    "claimed": 2,
    "acknowledged": 1,
    "failed": 1,
}:
    raise SystemExit(f"ERROR: scheduler metrics snapshot is invalid: {metrics_snapshot}")

for settings in (
    SchedulerSettings(poll_interval_seconds=0),
    SchedulerSettings(poll_interval_seconds=1, max_cycles=0),
):
    try:
        settings.validate()
    except SchedulerError:
        pass
    else:
        raise SystemExit("ERROR: invalid scheduler settings were accepted")

print("OK: scheduler validates positive polling and cycle bounds")
print("OK: scheduler executes a bounded polling cycle budget")
print("OK: scheduler aggregates claimed, acknowledged, and failed work")
print("OK: scheduler records idle polls and applies polling interval")
print("STATUS: PHASE 8 OUTBOX SCHEDULER READY")
