import asyncio
import os

from celery import Celery, shared_task
from sqlalchemy import create_engine, text

from services.api.sentry_config import init_sentry_if_configured as _init_sentry

from .client import fetch_fees
from .repository import upsert

_init_sentry()


def list_active_asins() -> list[str]:
    """Return known ASINs or an empty list if unavailable."""
    url = os.getenv("DATABASE_URL")
    if not url:
        return []
    engine = create_engine(url.replace("+asyncpg", "+psycopg"), future=True)
    try:
        with engine.begin() as conn:
            res = conn.execute(text("SELECT asin FROM products"))
            return [r[0] for r in res.fetchall()]
    except Exception:
        return []


app = Celery("fees_h10", broker=os.getenv("CELERY_BROKER_URL", "memory://"))

app.conf.beat_schedule = {
    "refresh-daily": {"task": "fees.refresh", "schedule": 86400.0}
}


@shared_task(name="fees.refresh")  # type: ignore[misc]
def refresh_fees() -> None:
    asins = list_active_asins()
    asyncio.run(_bulk(asins))


async def _bulk(asins: list[str]) -> None:
    for a in asins:
        row = await fetch_fees(a)
        await upsert(row)
