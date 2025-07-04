from typing import List, AsyncGenerator
import asyncio
import os
from fastapi import Depends, FastAPI
from sqlalchemy import bindparam, text

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/awa.db")

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
    echo=False,
)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


app = FastAPI()


@app.on_event("startup")
async def _wait_for_db() -> None:
    """Block application startup until the database becomes available."""
    delay = 0.2
    for _ in range(10):
        try:
            async for session in get_session():
                await session.execute(text("SELECT 1"))
            return
        except Exception:
            await asyncio.sleep(delay)
    raise RuntimeError("Database not available")


@app.get("/health")
async def health(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"db": "ok"}


@app.post("/score")
async def score(asins: List[str], session: AsyncSession = Depends(get_session)):
    query = text(
        """
        SELECT p.asin, (p.price - o.cost) / o.cost AS roi
        FROM products p
        JOIN offers o ON p.asin = o.asin
        WHERE p.asin IN :asins
        ORDER BY roi DESC
        """
    ).bindparams(bindparam("asins", expanding=True))
    result = await session.execute(query, {"asins": tuple(asins)})
    rows = result.fetchall()
    return [{"asin": r[0], "roi": r[1]} for r in rows]
