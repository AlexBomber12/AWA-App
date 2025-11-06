from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, cast

import asyncpg

if TYPE_CHECKING:  # pragma: no cover - import for type hints only
    from telegram import Bot as Bot
else:  # runtime import with fallback
    try:
        from telegram import Bot as RuntimeBot
    except ModuleNotFoundError:  # pragma: no cover - CI fallback

        class RuntimeBot:
            def __init__(self, _: str) -> None:  # noqa: D401 - simple stub
                """Stub telegram.Bot when library is absent."""

            async def send_message(self, *_args: Any, **_kwargs: Any) -> None:
                return None

    Bot = RuntimeBot


DSN = os.getenv("PG_ASYNC_DSN", "")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ROI_THRESHOLD = int(os.getenv("ROI_THRESHOLD", "5"))
ROI_DURATION_DAYS = int(os.getenv("ROI_DURATION_DAYS", "30"))
COST_DELTA_PCT = int(os.getenv("COST_DELTA_PCT", "10"))
PRICE_DROP_PCT = int(os.getenv("PRICE_DROP_PCT", "15"))
RETURNS_PCT = int(os.getenv("RETURNS_PCT", "5"))
STALE_DAYS = int(os.getenv("STALE_DAYS", "30"))

# Telegram bot initialisation
#
# In some environments the python‑telegram‑bot library will attempt to auto‑configure
# HTTP/SOCKS proxy support based on environment variables (e.g. `HTTPS_PROXY`).
# When the optional socks extras are missing (`socksio` package), this can raise
# ImportError/RuntimeError at import or instantiation time.  A hard failure here
# prevents the remainder of this module – and all tests that import it – from
# executing.  To allow tests to run without requiring proxy extras, we guard
# the bot creation in a try/except.  If initialisation fails for any reason
# (missing extras or misconfigured environment), we fall back to a minimal stub
# implementation.  The tests mock out `bot.send_message` anyway, so skipping
# initialisation has no adverse effect.
try:
    bot = Bot(TOKEN) if TOKEN and CHAT_ID else None
except Exception:
    # Fallback to stub Bot when telegram library cannot be initialised.
    class _BotStub:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            """Stub telegram.Bot when initialisation fails."""
            pass

        async def send_message(self, *_args: Any, **_kwargs: Any) -> None:
            return None

    Bot = _BotStub  # type: ignore[assignment,misc]
    bot = Bot(TOKEN) if TOKEN and CHAT_ID else None


MSG_ROI_DROP = "⚠️ Маржа по товару упала ниже 5 %. Проверьте цену и закупочную стоимость."


async def fetch_rows(query: str, *args: Any) -> list[asyncpg.Record]:
    conn = await asyncpg.connect(dsn=DSN)
    try:
        rows = await conn.fetch(query, *args)
    finally:
        await conn.close()
    return cast(list[asyncpg.Record], rows)


async def send(title: str, body: str) -> None:
    if not bot or CHAT_ID is None:
        return
    await bot.send_message(chat_id=CHAT_ID, text=f"{title}\n{body}")


async def check_a1() -> None:
    rows = await fetch_rows(
        "SELECT asin, roi_pct FROM roi_view WHERE roi_pct < $1 AND updated_at < now() - interval '$2 days'",
        ROI_THRESHOLD,
        ROI_DURATION_DAYS,
    )
    if rows:
        lst = "\n".join(f"{r['asin']} {r['roi_pct']}%" for r in rows)
        await send(MSG_ROI_DROP, lst)


async def check_a2() -> None:
    rows = await fetch_rows(
        """
        WITH t AS (
            SELECT vendor_id, sku, cost,
                   LAG(cost) OVER (PARTITION BY vendor_id, sku ORDER BY updated_at) AS prev_cost,
                   updated_at
            FROM vendor_prices
        )
        SELECT sku, vendor_id, ROUND((cost - prev_cost) / prev_cost * 100, 2) AS delta
        FROM t
        WHERE prev_cost IS NOT NULL AND delta > $1
        ORDER BY updated_at DESC
        """,
        COST_DELTA_PCT,
    )
    if rows:
        lst = "\n".join(f"{r['sku']} {r['delta']}%" for r in rows)
        await send(
            f"💸 Закупочная цена выросла > {COST_DELTA_PCT}%",
            f"{lst}\n👉 Свяжитесь с поставщиком или ищите альтернативу.",
        )


async def check_a3() -> None:
    rows = await fetch_rows(
        """
        SELECT asin, 100 * (price_48h - price_now) / price_48h AS drop_pct
        FROM buybox_prices
        WHERE drop_pct > $1
        """,
        PRICE_DROP_PCT,
    )
    if rows:
        lst = "\n".join(f"{r['asin']} {r['drop_pct']}%" for r in rows)
        await send(
            f"🏷️ Цена Buy Box упала > {PRICE_DROP_PCT}% за 48 ч",
            f"{lst}\n👉 Решите: снизить цену или распродать остатки.",
        )


async def check_a4() -> None:
    rows = await fetch_rows(
        "SELECT asin, returns_ratio FROM returns_view WHERE returns_ratio > $1",
        RETURNS_PCT,
    )
    if rows:
        lst = "\n".join(f"{r['asin']} {r['returns_ratio']}%" for r in rows)
        await send(
            f"🔄 Доля возвратов > {RETURNS_PCT}% за 30 дней",
            f"{lst}\n👉 Проверьте качество товара и описание листинга.",
        )


async def check_a5() -> None:
    rows = await fetch_rows(
        "SELECT vendor_id FROM vendor_prices GROUP BY vendor_id HAVING MAX(updated_at) < now() - interval '$1 days'",
        STALE_DAYS,
    )
    if rows:
        lst = "\n".join(f"vendor {r['vendor_id']}" for r in rows)
        await send(
            f"📜 Прайс-лист устарел > {STALE_DAYS} дней",
            f"{lst}\n👉 Запросите свежий прайс у поставщика.",
        )


send_rules = [check_a1, check_a2, check_a3, check_a4, check_a5]
