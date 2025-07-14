from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from services.common.db_url import build_url


ENGINE: AsyncEngine | None = None


async def init_db() -> None:
    global ENGINE
    if ENGINE is None:
        ENGINE = create_async_engine(build_url(async_=True), future=True)
    async with ENGINE.begin() as conn:
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS freight_rates (
                    lane TEXT,
                    mode TEXT,
                    eur_per_kg NUMERIC(10,2),
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (lane, mode)
                );
                """
            )
        )


async def dispose() -> None:
    if ENGINE is not None:
        await ENGINE.dispose()
