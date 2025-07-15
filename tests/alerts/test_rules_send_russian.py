import importlib
import os
import types

import pytest

# ensure env vars for bot
os.environ.setdefault("TELEGRAM_TOKEN", "t")
os.environ.setdefault("TELEGRAM_CHAT_ID", "1")

alert_bot = importlib.import_module("services.alert_bot.alert_bot")

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "func,rows,keyword",
    [
        (alert_bot.check_a1, [{"asin": "A1", "roi_pct": 4}], "ROI ниже"),
        (alert_bot.check_a2, [{"sku": "S1", "delta": 12}], "Закупочная"),
        (alert_bot.check_a3, [{"asin": "A2", "drop_pct": 20}], "Buy Box"),
        (alert_bot.check_a4, [{"asin": "A3", "returns_ratio": 7}], "возвратов"),
        (alert_bot.check_a5, [{"vendor_id": 1}], "Прайс-лист"),
    ],
)
async def test_rules_send_russian(monkeypatch, func, rows, keyword):
    messages = []

    async def fake_fetch(*a, **k):
        return rows

    async def fake_send_message(self, chat_id, text):
        messages.append(text)

    monkeypatch.setattr(alert_bot, "fetch_rows", fake_fetch)
    monkeypatch.setattr(alert_bot.Bot, "send_message", fake_send_message)

    await func()

    assert len(messages) == 1
    assert keyword in messages[0]
