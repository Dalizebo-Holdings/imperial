from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Callable


class HealthCheckError(ValueError):
    pass


@dataclass(frozen=True)
class HealthResult:
    name: str
    required: bool
    healthy: bool
    details: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class HealthRegistry:
    def __init__(self) -> None:
        self._checks: dict[
            str,
            tuple[bool, Callable[[], HealthResult]],
        ] = {}

    def register(
        self,
        name: str,
        check: Callable[[], HealthResult],
        *,
        required: bool = True,
    ) -> None:
        normalized = str(name).strip()

        if not normalized:
            raise HealthCheckError(
                "health check name must not be empty"
            )

        if normalized in self._checks:
            raise HealthCheckError(
                f"health check already registered: {normalized}"
            )

        if not callable(check):
            raise HealthCheckError(
                "health check must be callable"
            )

        self._checks[normalized] = (
            bool(required),
            check,
        )

    def evaluate(self) -> dict:
        results = []

        for name in sorted(self._checks):
            required, check = self._checks[name]

            try:
                raw = check()
            except Exception:
                raw = HealthResult(
                    name=name,
                    required=required,
                    healthy=False,
                    details="health check failed safely",
                )

            if not isinstance(raw, HealthResult):
                raise HealthCheckError(
                    f"health check {name} returned invalid result"
                )

            result = HealthResult(
                name=name,
                required=required,
                healthy=raw.healthy,
                details=raw.details,
            )
            results.append(result)

        readiness = all(
            result.healthy
            for result in results
            if result.required
        )

        return {
            "live": True,
            "ready": readiness,
            "checks": [
                result.to_dict()
                for result in results
            ],
        }
