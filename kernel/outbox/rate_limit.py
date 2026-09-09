from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from kernel.outbox.runtime import ClaimedOutboxEvent


class OutboxRateLimitError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RateLimitSettings:
    capacity: int
    refill_seconds: int
    max_wait_seconds: int

    def validate(self) -> None:
        if self.capacity < 1:
            raise OutboxRateLimitError("capacity must be >= 1")
        if self.refill_seconds < 1:
            raise OutboxRateLimitError("refill_seconds must be >= 1")
        if self.max_wait_seconds < 0:
            raise OutboxRateLimitError("max_wait_seconds must be >= 0")


class RateLimitOutcome(Protocol):
    @property
    def allowed(self) -> bool: ...

    @property
    def remaining(self) -> int: ...

    @property
    def retry_after_seconds(self) -> int | None: ...

    @property
    def evaluated_at(self) -> str: ...


@dataclass(frozen=True, slots=True)
class RateLimitAllowance:
    allowed: bool
    remaining: int
    retry_after_seconds: int | None
    evaluated_at: str


@dataclass(frozen=True, slots=True)
class OutboxRateLimiter(Protocol):
    def check(
        self,
        *,
        worker_id: str,
        organization_id: str,
        event_id: str,
        attempt_count: int,
    ) -> RateLimitOutcome: ...


class TokenBucketRateLimiter:
    def __init__(
        self,
        *,
        capacity: int,
        refill_seconds: int,
        max_wait_seconds: int = 0,
        now: datetime | None = None,
    ) -> None:
        settings = RateLimitSettings(
            capacity=capacity,
            refill_seconds=refill_seconds,
            max_wait_seconds=max_wait_seconds,
        )
        settings.validate()
        self._capacity = capacity
        self._refill_seconds = refill_seconds
        self._max_wait_seconds = max_wait_seconds
        self._tokens = float(capacity)
        self._last_refill = now or datetime.now(timezone.utc)

    def check(
        self,
        *,
        worker_id: str,
        organization_id: str,
        event_id: str,
        attempt_count: int,
    ) -> RateLimitOutcome:
        if not worker_id.strip() or not organization_id.strip() or not event_id.strip():
            raise OutboxRateLimitError("worker_id/organization_id/event_id required")
        if attempt_count < 1:
            raise OutboxRateLimitError("attempt_count must be >= 1")

        self._refill(now=datetime.now(timezone.utc))
        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return RateLimitAllowance(
                allowed=True,
                remaining=max(0, int(self._tokens)),
                retry_after_seconds=None,
                evaluated_at=self._last_refill.isoformat(),
            )
        return RateLimitAllowance(
            allowed=False,
            remaining=0,
            retry_after_seconds=self._next_fill_seconds(),
            evaluated_at=self._last_refill.isoformat(),
        )

    def _refill(self, *, now: datetime) -> None:
        elapsed = (now - self._last_refill).total_seconds()
        if elapsed <= 0:
            return
        added = elapsed / self._refill_seconds
        self._tokens = min(float(self._capacity), self._tokens + added)
        self._last_refill = now

    def _next_fill_seconds(self) -> int:
        deficit = 1.0 - self._tokens
        return max(1, int(deficit * self._refill_seconds))
