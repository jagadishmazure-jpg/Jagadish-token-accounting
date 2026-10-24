"""Sliding one-second window request limiter (100 requests per second by default)."""

from __future__ import annotations

from collections import deque


class RequestRateLimiter:
    def __init__(self, rps: int = 100) -> None:
        if rps <= 0:
            raise ValueError("rps must be positive")
        self.rps = rps
        self._hits: deque[float] = deque()

    def allow(self, now: float) -> bool:
        while self._hits and now - self._hits[0] >= 1.0:
            self._hits.popleft()
        if len(self._hits) >= self.rps:
            return False
        self._hits.append(now)
        return True
