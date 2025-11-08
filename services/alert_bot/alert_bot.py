import asyncio
import os

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from awa_common.logging import configure_logging

from .rules import bot, check_a1, check_a2, check_a3, check_a4, check_a5, init_db_pool

configure_logging(service="alert_bot")
logger = structlog.get_logger(__name__).bind(component="alert_bot")

scheduler = AsyncIOScheduler(timezone="UTC")

CHECK_INTERVAL_MIN = int(os.getenv("CHECK_INTERVAL_MIN", "60"))


def start() -> int:
    if not bot:
        logger.info("alerts.disabled")
        return 0
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db_pool())
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
