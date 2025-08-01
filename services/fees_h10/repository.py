from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from services.common.dsn import build_dsn

_engine: AsyncEngine | None = None


def _get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(build_dsn(sync=False), future=True)
    return _engine


async def upsert(row: Dict[str, Any]) -> None:
    query = text(
        """
        INSERT INTO fees_raw (asin, fulfil_fee, referral_fee, storage_fee, currency)
        VALUES (:asin, :fulfil_fee, :referral_fee, :storage_fee, :currency)
        ON CONFLICT (asin) DO UPDATE SET
          fulfil_fee = EXCLUDED.fulfil_fee,
          referral_fee = EXCLUDED.referral_fee,
          storage_fee = EXCLUDED.storage_fee,
          currency = EXCLUDED.currency,
          updated_at = CURRENT_TIMESTAMP
        """
    )
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.execute(query, row)
