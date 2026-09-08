from __future__ import annotations

from collections import defaultdict
import re
from typing import Iterable


class MetricsError(ValueError):
    pass


def _metric_key(
    name: str,
    labels: dict[str, str] | None,
) -> tuple[str, tuple[tuple[str, str], ...]]:
    metric_name = str(name).strip()

    if not re.fullmatch(
        r"[a-zA-Z_:][a-zA-Z0-9_:.-]{1,127}",
        metric_name,
    ):
        raise MetricsError(
            f"invalid metric name: {metric_name}"
        )

    normalized = tuple(
        sorted(
            (
                str(key).strip(),
                str(value).strip(),
            )
            for key, value in (labels or {}).items()
        )
    )

    if any(not key or not value for key, value in normalized):
        raise MetricsError(
            "metric labels must have non-empty keys and values"
        )

    return metric_name, normalized


class MetricRegistry:
    def __init__(self) -> None:
        self._counters = defaultdict(float)
        self._gauges = {}
        self._timings = defaultdict(list)

    def increment(
        self,
        name: str,
        value: float = 1.0,
        *,
        labels: dict[str, str] | None = None,
    ) -> float:
        if value < 0:
            raise MetricsError(
                "counter increments must be non-negative"
            )
        key = _metric_key(name, labels)
        self._counters[key] += float(value)
        return self._counters[key]

    def set_gauge(
        self,
        name: str,
        value: float,
        *,
        labels: dict[str, str] | None = None,
    ) -> float:
        key = _metric_key(name, labels)
        self._gauges[key] = float(value)
        return self._gauges[key]

    def observe(
        self,
        name: str,
        value: float,
        *,
        labels: dict[str, str] | None = None,
    ) -> None:
        if value < 0:
            raise MetricsError(
                "timing observations must be non-negative"
            )
        key = _metric_key(name, labels)
        self._timings[key].append(float(value))

    def snapshot(self) -> dict:
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "timings": {
                key: {
                    "count": len(values),
                    "sum": sum(values),
                    "min": min(values),
                    "max": max(values),
                }
                for key, values in self._timings.items()
                if values
            },
        }
