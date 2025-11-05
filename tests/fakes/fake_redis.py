from __future__ import annotations

import time


class FakeRedis:
    """Minimal async Redis double compatible with fastapi-limiter."""

    def __init__(self) -> None:
        # key -> (window_ms, reset_at_ms, count)
        self._state: dict[str, tuple[int, int, int]] = {}

    async def evalsha(self, sha: str, numkeys: int, key: str, times: str, milliseconds: str) -> int:
        limit = int(times)
        window_ms = int(milliseconds)
        now_ms = int(time.monotonic() * 1000)

        entry = self._state.get(key)
        if entry is None or now_ms >= entry[1]:
            entry = (window_ms, now_ms + window_ms, 0)

        window_ms, reset_at_ms, count = entry
        if count < limit:
            self._state[key] = (window_ms, reset_at_ms, count + 1)
            return 0

        ttl = max(1, reset_at_ms - now_ms)
        self._state[key] = (window_ms, reset_at_ms, count)
        return ttl

    async def ping(self) -> bool:
        return True

    async def script_load(self, script: str) -> str:  # noqa: ARG002 - parity with redis
        return "fake-sha"

    def reset(self) -> None:
        self._state.clear()


__all__ = ["FakeRedis"]
