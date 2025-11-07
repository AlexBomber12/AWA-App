from __future__ import annotations

import asyncio

import pytest


def test_start_returns_zero_when_bot_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.alert_bot import alert_bot

    monkeypatch.setattr(alert_bot, "bot", None, raising=False)

    assert alert_bot.start() == 0


def test_start_initialises_pool_and_schedules(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.alert_bot import alert_bot

    jobs: list[tuple[str, dict[str, object]]] = []

    class DummyScheduler:
        def add_job(self, fn, trigger, **kwargs):  # pragma: no cover - invoked via test only
            jobs.append((trigger, {"fn": fn, **kwargs}))

        def start(self):
            jobs.append(("started", {}))

    async def fake_init_db_pool():
        return object()

    class DummyLoop:
        def __init__(self) -> None:
            self.called = False

        def run_until_complete(self, coro):
            self.called = True
            return asyncio.run(coro)

    dummy_loop = DummyLoop()

    monkeypatch.setattr(alert_bot, "bot", object(), raising=False)
    monkeypatch.setattr(alert_bot, "scheduler", DummyScheduler(), raising=False)
    monkeypatch.setattr(alert_bot, "init_db_pool", fake_init_db_pool, raising=False)
    monkeypatch.setattr(alert_bot.asyncio, "get_event_loop", lambda: dummy_loop)

    assert alert_bot.start() == 1
    assert dummy_loop.called is True
    triggers = {trigger for trigger, _ in jobs}
    assert {"interval", "cron", "started"}.issubset(triggers)
