from __future__ import annotations

import asyncio
import importlib

import pytest


def _reload_worker_module():
    module = importlib.import_module("services.worker.celery_app")
    stop = getattr(module, "_stop_worker_loop_lag_monitor", None)
    if callable(stop):
        stop()
    return importlib.reload(module)


def test_import_does_not_start_monitor(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("CELERY_LOOP_LAG_MONITOR", raising=False)
    module = _reload_worker_module()
    assert module.is_loop_lag_monitor_active() is False


def test_disabled_env_blocks_manual_start(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CELERY_LOOP_LAG_MONITOR", "0")
    module = _reload_worker_module()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        module._start_worker_loop_lag_monitor()
        assert module.is_loop_lag_monitor_active() is False
    finally:
        module._stop_worker_loop_lag_monitor()
        loop.close()
        asyncio.set_event_loop(None)
