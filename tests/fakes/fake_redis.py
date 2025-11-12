from __future__ import annotations

import asyncio
import fnmatch
import time
from typing import Any


class FakeRedis:
    """Async Redis test double with minimal caching semantics."""

    def __init__(self) -> None:
        # rate limit state -> key -> (window_ms, reset_at_ms, count)
        self._state: dict[str, tuple[int, int, int]] = {}
        self._data: dict[str, Any] = {}
        self._exp: dict[str, float] = {}
        self._kv = self._data  # backward compatibility for legacy tests
        self._lock = asyncio.Lock()

    async def evalsha(self, sha: str, numkeys: int, key: str, times: str, milliseconds: str) -> int:
        limit = int(times)
        window_ms = int(milliseconds)
        now_ms = int(self._now() * 1000)

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

    async def incr(self, key: str) -> int:
        await self._purge()
        async with self._lock:
            val = int(self._data.get(key, 0)) + 1
            self._data[key] = val
            return val

    async def expire(self, key: str, seconds: int) -> bool:
        await self._purge()
        async with self._lock:
            if key not in self._data:
                return False
            self._exp[key] = self._now() + int(seconds)
            return True

    async def ttl(self, key: str) -> int:
        await self._purge()
        if key not in self._data:
            return -2
        expires = self._exp.get(key)
        if expires is None:
            return -1
        remaining = int(expires - self._now())
        return remaining if remaining >= 0 else -2

    async def get(self, key: str) -> Any | None:
        await self._purge()
        return self._data.get(key)

    async def set(self, key: str, value: Any, ex: int | None = None, px: int | None = None) -> bool:
        await self._purge()
        ttl: float | None = None
        if px is not None:
            ttl = float(px) / 1000.0
        elif ex is not None:
            ttl = float(ex)
        async with self._lock:
            self._data[key] = value
            if ttl is None or ttl <= 0:
                self._exp.pop(key, None)
            else:
                self._exp[key] = self._now() + ttl
        return True

    async def setex(self, key: str, time_s: int, value: Any) -> bool:
        return await self.set(key, value, ex=time_s)

    async def delete(self, *keys: str) -> int:
        await self._purge()
        removed = 0
        async with self._lock:
            for key in keys:
                if key in self._data:
                    removed += 1
                    self._data.pop(key, None)
                    self._exp.pop(key, None)
        return removed

    async def scan_iter(self, match: str | None = None, count: int | None = None):  # noqa: ARG002 - parity
        await self._purge()
        for key in list(self._data.keys()):
            if key in self._data and (match is None or fnmatch.fnmatch(key, match)):
                yield key

    async def flushall(self) -> None:
        async with self._lock:
            self._state.clear()
            self._data.clear()
            self._exp.clear()

    async def aclose(self) -> None:
        return None

    def reset(self) -> None:
        self._state.clear()
        self._data.clear()
        self._exp.clear()

    async def _purge(self) -> None:
        now = self._now()
        for key, expires in list(self._exp.items()):
            if expires <= now:
                self._data.pop(key, None)
                self._exp.pop(key, None)

    def pipeline(self, transaction: bool = False):  # noqa: ARG002 - parity with redis
        return _FakePipeline(self)

    def _now(self) -> float:
        return time.monotonic()


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
