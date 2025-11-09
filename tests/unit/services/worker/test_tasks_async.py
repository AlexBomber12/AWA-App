from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

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


def test_resolve_async_to_sync_uses_import(monkeypatch: pytest.MonkeyPatch) -> None:
    def dummy(func):
        return func

    monkeypatch.setattr(tasks, "_asgiref_async_to_sync", None, raising=False)
    monkeypatch.setattr(tasks.importlib, "import_module", lambda name: SimpleNamespace(async_to_sync=dummy))

    resolved = tasks._resolve_async_to_sync()
    assert resolved is dummy


def test_resolve_async_to_sync_fallback_when_import_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tasks, "_asgiref_async_to_sync", None, raising=False)

    def boom(name):
        raise ModuleNotFoundError

    monkeypatch.setattr(tasks.importlib, "import_module", boom)
    resolved = tasks._resolve_async_to_sync()
    assert resolved is tasks._fallback_async_to_sync


def test_celery_wrapper_evaluate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tasks, "_evaluate_alerts_sync", lambda: {"ok": 1})
    assert tasks.evaluate_alert_rules() == {"ok": 1}


def test_celery_wrapper_health(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tasks.alerts_worker, "alert_rules_health", lambda: {"enabled": True})
    assert tasks.alert_rules_health()["enabled"] is True
