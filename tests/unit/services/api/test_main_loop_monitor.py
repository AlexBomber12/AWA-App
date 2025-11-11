from __future__ import annotations

import asyncio

import pytest

from services.api import main as main_module


@pytest.mark.asyncio
async def test_lifespan_starts_loop_monitor(monkeypatch):
    calls: dict[str, bool] = {"started": False, "stopped": False}

    async def _noop(*_a, **_k) -> None:
        return None

    async def _wait_for_redis(_url: str) -> None:
        return None

    monkeypatch.setattr(main_module, "init_async_engine", _noop)
    monkeypatch.setattr(main_module, "dispose_async_engine", _noop)
    monkeypatch.setattr(main_module, "_wait_for_db", _noop)
    monkeypatch.setattr(main_module, "_check_llm", _noop)
    monkeypatch.setattr(main_module, "_wait_for_redis", _wait_for_redis)
    monkeypatch.setattr(main_module.FastAPILimiter, "init", _noop)
    monkeypatch.setattr(main_module.FastAPILimiter, "close", _noop)

    def fake_start(loop, interval_s=1.0):
        assert isinstance(loop, asyncio.AbstractEventLoop)
        calls["started"] = True

        def _stop():
            calls["stopped"] = True

        return _stop

    monkeypatch.setattr(main_module, "start_loop_lag_monitor", fake_start)
    monkeypatch.setattr(main_module.settings, "ENABLE_LOOP_LAG_MONITOR", True)
    monkeypatch.setattr(main_module.settings, "LOOP_LAG_INTERVAL_S", 0.01)

    async with main_module.lifespan(main_module.app):
        assert calls["started"] is True
    assert calls["stopped"] is True
