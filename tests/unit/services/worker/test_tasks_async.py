from __future__ import annotations

import asyncio

from services.worker import tasks


def test_fallback_async_to_sync_runs_coroutine() -> None:
    calls: list[int] = []

    async def _coro(value: int) -> str:
        await asyncio.sleep(0)
        calls.append(value)
        return f"done:{value}"

    sync_fn = tasks._fallback_async_to_sync(_coro)
    result = sync_fn(42)

    assert result == "done:42"
    assert calls == [42]
