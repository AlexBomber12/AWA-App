import asyncio
import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .rules import bot, check_a1, check_a2, check_a3, check_a4, check_a5

logging.basicConfig(level=logging.INFO)

scheduler = AsyncIOScheduler(timezone="UTC")

CHECK_INTERVAL_MIN = int(os.getenv("CHECK_INTERVAL_MIN", "60"))


def start() -> int:
    if not bot:
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
