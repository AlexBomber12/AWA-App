from typing import List
import asyncio
from fastapi import FastAPI
from sqlalchemy import text, bindparam

from db import AsyncSession

app = FastAPI()


@app.on_event("startup")
async def _wait_for_db() -> None:
    for _ in range(10):
        try:
            async with AsyncSession() as session:
                await session.execute(text("SELECT 1"))
            return
        except Exception:
            await asyncio.sleep(2)
    raise RuntimeError("Database not available")


@app.get("/health")
async def health() -> dict[str, str]:
    async with AsyncSession() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.post("/score")
async def score(asins: List[str]):
    query = text(
        """
        SELECT p.asin, (p.price - o.cost) / o.cost AS roi
        FROM product p
        JOIN offers o ON p.asin = o.asin
        WHERE p.asin IN :asins
        ORDER BY roi DESC
        """
    ).bindparams(bindparam("asins", expanding=True))
    async with AsyncSession() as session:
        result = await session.execute(query, {"asins": tuple(asins)})
        rows = result.fetchall()
    return [{"asin": r[0], "roi": r[1]} for r in rows]
