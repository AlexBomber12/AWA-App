from __future__ import annotations

import time


class FakeRedis:
    """Minimal async Redis double compatible with fastapi-limiter."""

    def __init__(self) -> None:
        # key -> (window_ms, reset_at_ms, count)
        self._state: dict[str, tuple[int, float, int]] = {}

    async def evalsha(self, sha: str, numkeys: int, key: str, times: str, milliseconds: str) -> int:
        limit = int(times)
        window_ms = int(milliseconds)
        now_ms = int(time.monotonic() * 1000)

        window_ms_existing, reset_at_ms, count = window_ms, 0.0, 0
        st = self._state.get(key)
        if st:
            window_ms_existing, reset_at_ms, count = st
            window_ms = window_ms_existing or window_ms

        if not st or now_ms >= reset_at_ms:
            reset_at_ms = now_ms + window_ms
            count = 0

        if count < limit:
            count += 1
            self._state[key] = (window_ms, reset_at_ms, count)
            return 0

        ttl = max(1, int(reset_at_ms - now_ms))
        self._state[key] = (window_ms, reset_at_ms, count)
        return ttl

    async def ping(self) -> bool:
        return True

    async def script_load(self, *_args, **_kwargs) -> str:
        return "fake-sha"

    def reset(self) -> None:
        self._state.clear()


__all__ = ["FakeRedis"]
