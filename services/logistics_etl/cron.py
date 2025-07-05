from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .client import fetch_rates
from .repository import upsert_many


async def job() -> None:
    rows = await fetch_rates()
    await upsert_many(rows)


def start() -> None:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(job, "cron", hour=2)
    scheduler.start()
