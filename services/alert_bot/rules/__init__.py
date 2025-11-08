from __future__ import annotations

import asyncio
from typing import Any, cast

import asyncpg

from awa_common.dsn import build_dsn
from awa_common.settings import settings as SETTINGS
from awa_common.utils.env import env_str


# Database connection settings -------------------------------------------------
# Defaults keep cron jobs lightweight locally while allowing burstiness in prod.
def _first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value is None:
            continue
        stripped = value.strip()
        if stripped:
            return stripped
    return None


DSN = _first_non_empty(env_str("PG_ASYNC_DSN"), SETTINGS.PG_ASYNC_DSN) or build_dsn(sync=False)


ALERT_DB_POOL_MIN_SIZE = SETTINGS.ALERT_DB_POOL_MIN_SIZE
# Keep at most five concurrent rule queries by default to avoid starving API DB.
ALERT_DB_POOL_MAX_SIZE = max(ALERT_DB_POOL_MIN_SIZE, SETTINGS.ALERT_DB_POOL_MAX_SIZE)
# Abort connect attempts after 10s by default—the cron job retries later anyway.
ALERT_DB_POOL_TIMEOUT = SETTINGS.ALERT_DB_POOL_TIMEOUT
# Wait up to 3s for a pooled connection before retrying (prevents deadlocks).
ALERT_DB_POOL_ACQUIRE_TIMEOUT = SETTINGS.ALERT_DB_POOL_ACQUIRE_TIMEOUT
# Retry pool acquisition three times by default so transient spikes are absorbed.
ALERT_DB_POOL_ACQUIRE_RETRIES = max(1, SETTINGS.ALERT_DB_POOL_ACQUIRE_RETRIES)
# Short delay keeps pressure low when looping on pool contention.
ALERT_DB_POOL_RETRY_DELAY = SETTINGS.ALERT_DB_POOL_RETRY_DELAY

DB_POOL: asyncpg.Pool | None = None
_POOL_LOCK = asyncio.Lock()


async def init_db_pool() -> asyncpg.Pool:
    """Initialise (or return) the shared asyncpg connection pool."""

    global DB_POOL
    if DB_POOL is not None:
        return DB_POOL
    if not DSN:
        raise RuntimeError("PG_ASYNC_DSN is not configured")
    async with _POOL_LOCK:
        if DB_POOL is None:
            DB_POOL = await asyncpg.create_pool(
                dsn=DSN,
                min_size=ALERT_DB_POOL_MIN_SIZE,
                max_size=ALERT_DB_POOL_MAX_SIZE,
                timeout=ALERT_DB_POOL_TIMEOUT,
            )
    if DB_POOL is None:  # pragma: no cover - defensive only
        raise RuntimeError("Database pool initialisation failed")
    return DB_POOL


async def close_db_pool() -> None:
    """Close the shared asyncpg pool when the bot shuts down."""

    global DB_POOL
    pool = DB_POOL
    if pool is None:
        return
    DB_POOL = None
    await pool.close()


async def fetch_rows(query: str, *args: Any) -> list[asyncpg.Record]:
    pool = await init_db_pool()
    last_exc: Exception | None = None
    for attempt in range(1, ALERT_DB_POOL_ACQUIRE_RETRIES + 1):
        try:
            async with pool.acquire(timeout=ALERT_DB_POOL_ACQUIRE_TIMEOUT) as conn:
                rows = await conn.fetch(query, *args)
                return cast(list[asyncpg.Record], rows)
        except (TimeoutError, asyncpg.PostgresError) as exc:
            last_exc = exc
            if attempt >= ALERT_DB_POOL_ACQUIRE_RETRIES:
                raise
            await asyncio.sleep(ALERT_DB_POOL_RETRY_DELAY)
    if last_exc:  # pragma: no cover - loop ensures raise above
        raise last_exc
    return []


async def query_roi_breaches(min_roi_pct: float, min_duration_days: int) -> list[asyncpg.Record]:
    return await fetch_rows(
        "SELECT asin, roi_pct FROM roi_view WHERE roi_pct < $1 AND updated_at < now() - interval '$2 days'",
        min_roi_pct,
        min_duration_days,
    )


async def query_price_increase(delta_pct: float) -> list[asyncpg.Record]:
    return await fetch_rows(
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
        delta_pct,
    )


async def query_buybox_drop(drop_pct: float) -> list[asyncpg.Record]:
    return await fetch_rows(
        """
        SELECT asin, 100 * (price_48h - price_now) / price_48h AS drop_pct
        FROM buybox_prices
        WHERE drop_pct > $1
        """,
        drop_pct,
    )


async def query_high_returns(returns_pct: float) -> list[asyncpg.Record]:
    return await fetch_rows(
        "SELECT asin, returns_ratio FROM returns_view WHERE returns_ratio > $1",
        returns_pct,
    )


async def query_stale_price_lists(stale_days: int) -> list[asyncpg.Record]:
    return await fetch_rows(
        "SELECT vendor_id FROM vendor_prices GROUP BY vendor_id HAVING MAX(updated_at) < now() - interval '$1 days'",
        stale_days,
    )
