import asyncio
import logging
import os
from typing import Any

import asyncpg
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot

logging.basicConfig(level=logging.INFO)

DSN = os.getenv("PG_ASYNC_DSN", "")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ROI_THRESHOLD = int(os.getenv("ROI_THRESHOLD", "5"))
ROI_DURATION_DAYS = int(os.getenv("ROI_DURATION_DAYS", "30"))
COST_DELTA_PCT = int(os.getenv("COST_DELTA_PCT", "10"))
PRICE_DROP_PCT = int(os.getenv("PRICE_DROP_PCT", "15"))
RETURNS_PCT = int(os.getenv("RETURNS_PCT", "5"))
STALE_DAYS = int(os.getenv("STALE_DAYS", "30"))
CHECK_INTERVAL_MIN = int(os.getenv("CHECK_INTERVAL_MIN", "60"))

bot = Bot(TOKEN) if TOKEN and CHAT_ID else None
scheduler = AsyncIOScheduler(timezone="UTC")


async def fetch_rows(query: str, *args: Any) -> list[asyncpg.Record]:
    conn = await asyncpg.connect(dsn=DSN)
    try:
        rows = await conn.fetch(query, *args)
    finally:
        await conn.close()
    return rows


async def send(title: str, body: str) -> None:
    if not bot:
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
        await send(
            f"⚠️ ROI ниже {ROI_THRESHOLD}% уже {ROI_DURATION_DAYS} дней",
            f"{lst}\n👉 Проверьте себестоимость и цену продажи.",
        )


async def check_a2() -> None:
    rows = await fetch_rows(
        """
        WITH t AS (
            SELECT
                vendor_id,
                sku,
                cost,
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
        """
        SELECT asin, returns_ratio
        FROM returns_view
        WHERE returns_ratio > $1
        """,
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
        "SELECT vendor_id, MAX(updated_at) AS ts FROM vendor_prices GROUP BY vendor_id HAVING MAX(updated_at) < now() - interval '$1 days'",
        STALE_DAYS,
    )
    if rows:
        lst = "\n".join(f"vendor {r['vendor_id']}" for r in rows)
        await send(
            f"📜 Прайс-лист устарел > {STALE_DAYS} дней",
            f"{lst}\n👉 Запросите свежий прайс у поставщика.",
        )


def start() -> int:
    if not (TOKEN and CHAT_ID):
        logging.info("ALERTS DISABLED")
        return 0
    scheduler.add_job(check_a1, "interval", minutes=CHECK_INTERVAL_MIN)
    scheduler.add_job(check_a2, "interval", minutes=CHECK_INTERVAL_MIN)
    scheduler.add_job(check_a3, "interval", minutes=CHECK_INTERVAL_MIN)
    scheduler.add_job(check_a4, "cron", hour=3)
    scheduler.add_job(check_a5, "cron", hour=4)
    scheduler.start()
    return 1


if __name__ == "__main__":
    if start():
        asyncio.get_event_loop().run_forever()
