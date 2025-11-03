from __future__ import annotations

import importlib
import sys
import types

import pytest


def _load_rules(monkeypatch: pytest.MonkeyPatch, **env: str) -> types.ModuleType:
    """Reload the alert rules module with controlled environment variables."""
    for key in ("TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID"):
        if key not in env:
            monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    sys.modules.pop("services.alert_bot.rules", None)
    return importlib.import_module("services.alert_bot.rules")


@pytest.mark.asyncio
async def test_check_a1_triggers_send_on_low_roi(monkeypatch: pytest.MonkeyPatch) -> None:
    rules = _load_rules(monkeypatch)

    calls: dict[str, object] = {}

    async def fake_fetch(query: str, *args):
        calls["query"] = query
        calls["args"] = args
        return [{"asin": "SKU-1", "roi_pct": 3}]

    async def fake_send(title: str, body: str) -> None:
        calls["title"] = title
        calls["body"] = body

    monkeypatch.setattr(rules, "fetch_rows", fake_fetch)
    monkeypatch.setattr(rules, "send", fake_send)

    await rules.check_a1()

    assert calls["args"] == (
        rules.ROI_THRESHOLD,
        rules.ROI_DURATION_DAYS,
    )
    assert "SKU-1 3%" in calls["body"]


@pytest.mark.asyncio
async def test_check_a1_skips_when_threshold_not_breached(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rules = _load_rules(monkeypatch)

    async def fake_fetch(query: str, *args):
        # The DB would return nothing when values land exactly on the threshold.
        assert args[0] == rules.ROI_THRESHOLD
        assert args[1] == rules.ROI_DURATION_DAYS
        return []

    send_called = False

    async def fake_send(*_args, **_kwargs):
        nonlocal send_called
        send_called = True

    monkeypatch.setattr(rules, "fetch_rows", fake_fetch)
    monkeypatch.setattr(rules, "send", fake_send)

    await rules.check_a1()

    assert send_called is False


@pytest.mark.asyncio
async def test_send_is_noop_when_bot_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    rules = _load_rules(monkeypatch)
    monkeypatch.setattr(rules, "bot", None)
    monkeypatch.setattr(rules, "CHAT_ID", None)

    await rules.send("ignored", "body")


@pytest.mark.asyncio
async def test_send_formats_message(monkeypatch: pytest.MonkeyPatch) -> None:
    rules = _load_rules(monkeypatch, TELEGRAM_TOKEN="token", TELEGRAM_CHAT_ID="123")

    captured: dict[str, object] = {}

    class DummyBot:
        async def send_message(self, chat_id: str, text: str) -> None:
            captured["chat_id"] = chat_id
            captured["text"] = text

    monkeypatch.setattr(rules, "bot", DummyBot())
    monkeypatch.setattr(rules, "CHAT_ID", "123")

    await rules.send("Title", "Line 1\nLine 2")

    assert captured["chat_id"] == "123"
    assert captured["text"] == "Title\nLine 1\nLine 2"


@pytest.mark.asyncio
async def test_bot_init_failure_falls_back_to_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    broken = types.ModuleType("telegram")

    class BrokenBot:
        def __init__(self, *_args, **_kwargs):
            raise RuntimeError("proxy missing")

    broken.Bot = BrokenBot  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "telegram", broken)
    rules = _load_rules(monkeypatch, TELEGRAM_TOKEN="token", TELEGRAM_CHAT_ID="999")

    assert hasattr(rules.bot, "send_message")

    await rules.send("Recovered", "Still works")
