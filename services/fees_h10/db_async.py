from __future__ import annotations

import asyncio
from collections.abc import Iterable, Sequence
from typing import Any

import asyncpg
import structlog

from awa_common.dsn import build_dsn
from awa_common.settings import settings as SETTINGS

logger = structlog.get_logger(__name__)

_POOL: asyncpg.Pool | None = None
_POOL_LOCK = asyncio.Lock()


async def init_pool() -> asyncpg.Pool:
    global _POOL
    if _POOL is not None:
        return _POOL
    async with _POOL_LOCK:
        if _POOL is None:
            dsn = SETTINGS.PG_ASYNC_DSN or build_dsn(sync=False)
            _POOL = await asyncpg.create_pool(
                dsn=dsn,
                min_size=1,
                max_size=max(1, SETTINGS.H10_DB_POOL_MAX_SIZE),
            )
    if _POOL is None:  # pragma: no cover
        raise RuntimeError("Failed to initialise asyncpg pool")
    return _POOL


async def close_pool() -> None:
    global _POOL
    pool = _POOL
    if pool is None:
        return
    _POOL = None
    await pool.close()


def _chunk_rows(rows: Sequence[dict[str, Any]], batch_size: int) -> Iterable[list[dict[str, Any]]]:
    for idx in range(0, len(rows), batch_size):
        yield list(rows[idx : idx + batch_size])


def _build_upsert_query(chunk: Sequence[dict[str, Any]]) -> tuple[str, list[Any]]:
    cols = ("asin", "fulfil_fee", "referral_fee", "storage_fee", "currency")
    placeholders: list[str] = []
    params: list[Any] = []
    for index, row in enumerate(chunk):
        base = index * len(cols)
        placeholders.append("(" + ", ".join(f"${base + offset + 1}" for offset in range(len(cols))) + ")")
        params.extend(row[col] for col in cols)

    values_sql = ", ".join(placeholders)
    query = f"""
    INSERT INTO fees_raw (asin, fulfil_fee, referral_fee, storage_fee, currency)
    VALUES {values_sql}
    ON CONFLICT (asin) DO UPDATE
      SET
        fulfil_fee = EXCLUDED.fulfil_fee,
        referral_fee = EXCLUDED.referral_fee,
        storage_fee = EXCLUDED.storage_fee,
        currency = EXCLUDED.currency,
        updated_at = NOW()
      WHERE fees_raw.fulfil_fee IS DISTINCT FROM EXCLUDED.fulfil_fee
         OR fees_raw.referral_fee IS DISTINCT FROM EXCLUDED.referral_fee
         OR fees_raw.storage_fee IS DISTINCT FROM EXCLUDED.storage_fee
         OR fees_raw.currency IS DISTINCT FROM EXCLUDED.currency
    RETURNING (xmax = 0) AS inserted_flag;
    """
    return query, params


async def upsert_fee_rows(rows: Sequence[dict[str, Any]], batch_size: int = 500) -> dict[str, int]:
    items = list(rows)
    if not items:
        return {"inserted": 0, "updated": 0}
    pool = await init_pool()
    inserted = 0
    updated = 0
    async with pool.acquire() as conn:
        for chunk in _chunk_rows(items, batch_size):
            query, params = _build_upsert_query(chunk)
            records = await conn.fetch(query, *params)
            new = sum(1 for record in records if record["inserted_flag"])
            inserted += new
            updated += len(records) - new
    logger.info(
        "fees_h10.db_batch",
        component="fees_h10",
        inserted=inserted,
        updated=updated,
    )
    return {"inserted": inserted, "updated": updated}
