from __future__ import annotations

import fnmatch
import time
from typing import Any


class FakeRedis:
    """Async Redis test double with minimal caching semantics."""

    def __init__(self) -> None:
        # rate limit state -> key -> (window_ms, reset_at_ms, count)
        self._state: dict[str, tuple[int, int, int]] = {}
        # general key store -> key -> (value, expires_at_monotonic | None)
        self._kv: dict[str, tuple[Any, float | None]] = {}

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

    async def get(self, key: str) -> Any | None:
        self._maybe_expire(key)
        entry = self._kv.get(key)
        return None if entry is None else entry[0]

    async def set(self, key: str, value: Any, ex: int | None = None, px: int | None = None) -> bool:
        ttl = None
        if px is not None:
            ttl = px / 1000.0
        elif ex is not None:
            ttl = float(ex)
        self._kv[key] = (value, self._expiry(ttl))
        return True

    async def setex(self, key: str, time_s: int, value: Any) -> bool:
        self._kv[key] = (value, self._expiry(float(time_s)))
        return True

    async def delete(self, *keys: str) -> int:
        removed = 0
        for key in keys:
            self._maybe_expire(key)
            if key in self._kv:
                del self._kv[key]
                removed += 1
        return removed

    async def expire(self, key: str, ttl: int) -> bool:
        if key not in self._kv:
            return False
        self._kv[key] = (self._kv[key][0], self._expiry(float(ttl)))
        return True

    async def ttl(self, key: str) -> int:
        self._maybe_expire(key)
        entry = self._kv.get(key)
        if entry is None:
            return -2
        expires_at = entry[1]
        if expires_at is None:
            return -1
        remaining = int(expires_at - time.monotonic())
        return remaining if remaining >= 0 else -2

    async def scan_iter(self, match: str | None = None, count: int | None = None):  # noqa: ARG002 - parity
        keys = list(self._kv.keys())
        for key in keys:
            self._maybe_expire(key)
            if key in self._kv and (match is None or fnmatch.fnmatch(key, match)):
                yield key

    def pipeline(self, transaction: bool = False):  # noqa: ARG002 - parity with redis
        return _FakePipeline(self)

    async def aclose(self) -> None:
        return None

    def reset(self) -> None:
        self._state.clear()
        self._kv.clear()

    def _maybe_expire(self, key: str) -> None:
        entry = self._kv.get(key)
        if entry is None:
            return
        expires_at = entry[1]
        if expires_at is None:
            return
        if time.monotonic() >= expires_at:
            del self._kv[key]

    @staticmethod
    def _expiry(ttl: float | None) -> float | None:
        if ttl is None or ttl <= 0:
            return None
        return time.monotonic() + ttl


class _FakePipeline:
    def __init__(self, client: FakeRedis) -> None:
        self.client = client
        self._ops: list[tuple[str, tuple[Any, ...]]] = []

    def delete(self, *keys: str) -> _FakePipeline:
        self._ops.append(("delete", keys))
        return self

    async def execute(self) -> list[int]:
        results: list[int] = []
        for op, args in self._ops:
            if op == "delete":
                results.append(await self.client.delete(*args))
        self._ops.clear()
        return results

    @property
    def command_stack(self) -> list[tuple[str, tuple[Any, ...]]]:
        return list(self._ops)


__all__ = ["FakeRedis"]
