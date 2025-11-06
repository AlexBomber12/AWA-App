from __future__ import annotations

import time
from collections.abc import Hashable


class InMemoryRateLimiter:
    """Tiny in-memory rate limiter used to avoid Redis in unit tests."""

    def __init__(self, *, default_limit: int = 100, default_window: float = 1.0) -> None:
        self.default_limit = default_limit
        self.default_window = default_window
        self._hits: dict[Hashable, list[float]] = {}

    def allow(self, key: Hashable, *, limit: int | None = None, window: float | None = None) -> bool:
        limit = limit or self.default_limit
        window = window or self.default_window
        if limit <= 0:
            return False
        if window <= 0:
            window = self.default_window
        now = time.monotonic()
        bucket = self._hits.setdefault(key, [])
        threshold = now - window
        bucket[:] = [ts for ts in bucket if ts >= threshold]
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True

    def reset(self, key: Hashable | None = None) -> None:
        if key is None:
            self._hits.clear()
        else:
            self._hits.pop(key, None)


__all__ = ["InMemoryRateLimiter"]
