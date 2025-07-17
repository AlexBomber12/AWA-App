import os

# ruff: noqa: E402
import pytest

respx = pytest.importorskip("respx")
pytestmark = pytest.mark.usefixtures("respx_mock")

# ensure env vars for bot
os.environ.setdefault("TELEGRAM_TOKEN", "t")  # noqa: E402
os.environ.setdefault("TELEGRAM_CHAT_ID", "1")  # noqa: E402

from services.alert_bot import rules


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "func,rows,keyword",
    [
        (rules.check_a1, [{"asin": "A1", "roi_pct": 4}], "Маржа"),
        (rules.check_a2, [{"sku": "S1", "delta": 12}], "Закупочная"),
        (rules.check_a3, [{"asin": "A2", "drop_pct": 20}], "Buy Box"),
        (rules.check_a4, [{"asin": "A3", "returns_ratio": 7}], "возвратов"),
        (rules.check_a5, [{"vendor_id": 1}], "Прайс-лист"),
    ],
)
async def test_rules_send_russian(monkeypatch, func, rows, keyword):
    messages = []

    async def fake_fetch(*a, **k):
        return rows

    async def fake_send_message(self, chat_id, text):
        messages.append(text)

    monkeypatch.setattr(rules, "fetch_rows", fake_fetch)
    monkeypatch.setattr(rules.Bot, "send_message", fake_send_message)

    await func()

    assert len(messages) == 1
    assert keyword in messages[0]
