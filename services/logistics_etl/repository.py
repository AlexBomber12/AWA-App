from __future__ import annotations

from typing import Iterable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from .dsn import build_dsn

_engine: AsyncEngine | None = None


def _get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(build_dsn(sync=False), future=True)
    return _engine


async def upsert_many(rows: Iterable[dict]) -> None:
    query = text(
        """
        INSERT INTO freight_rates (lane, mode, eur_per_kg)
        VALUES (:lane, :mode, :eur_per_kg)
        ON CONFLICT (lane, mode) DO UPDATE SET
          eur_per_kg = EXCLUDED.eur_per_kg,
          updated_at = CURRENT_TIMESTAMP
        """
    )
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.execute(query, list(rows))
