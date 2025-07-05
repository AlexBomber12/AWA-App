import asyncio
import os
from celery import Celery, shared_task

from services.common.keepa import list_active_asins
from .client import fetch_fees
from .repository import upsert

app = Celery(
    "fees_h10",
    broker=os.getenv("CELERY_BROKER_URL", "memory://"),
)

app.conf.beat_schedule = {
    "refresh-daily": {
        "task": "fees.refresh",
        "schedule": 86400.0,
    }
}


@shared_task(name="fees.refresh")  # type: ignore[misc]
def refresh_fees() -> None:
    asins = list_active_asins()
    asyncio.run(_bulk(asins))


async def _bulk(asins: list[str]) -> None:
    for a in asins:
        row = await fetch_fees(a)
        await upsert(row)
