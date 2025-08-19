import asyncio
import json
import logging
import os

import httpx
from celery import Celery, shared_task
from sqlalchemy import create_engine, text

try:
    # The worker can run as a standalone image where the full `services`
    # package is not present.  Import Sentry configuration if available but
    # fall back to a no-op in slim containers.
    from services.api.sentry_config import init_sentry_if_configured as _init_sentry
except ModuleNotFoundError:  # pragma: no cover - optional dependency

    def _init_sentry() -> None:
        """Initialize Sentry when the shared config is unavailable."""
        return None


from . import repository as repo
from .client import fetch_fees

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
    rows = []
    for a in asins:
        try:
            row = await fetch_fees(a)
            rows.append(row)
        except (
            httpx.TimeoutException,
            httpx.RequestError,
            json.JSONDecodeError,
            ValueError,
        ) as exc:
            logging.error("h10 fetch failed for %s: %s", a, exc)
    if not rows:
        return
    url = os.getenv("DATABASE_URL")
    if not url:
        return
    engine = create_engine(url.replace("+asyncpg", "+psycopg"), future=True)
    summary = repo.upsert_fees_raw(
        engine,
        rows,
        testing=os.getenv("TESTING") == "1",
    )
    if summary and os.getenv("TESTING") == "1":
        logging.info("h10 upsert summary %s", summary)
    engine.dispose()
