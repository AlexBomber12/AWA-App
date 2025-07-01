from typing import List
from fastapi import FastAPI
import asyncpg
import os

app = FastAPI()


@app.on_event("startup")
async def startup():
    app.state.pool = await asyncpg.create_pool(os.environ["DATABASE_URL"])


@app.on_event("shutdown")
async def shutdown():
    await app.state.pool.close()


@app.post("/score")
async def score(asins: List[str]):
    query = """
        SELECT p.asin, (p.price - o.cost) / o.cost AS roi
        FROM product p
        JOIN offers o ON p.asin = o.asin
        WHERE p.asin = ANY($1::text[])
        ORDER BY roi DESC
    """
    rows = await app.state.pool.fetch(query, asins)
    return [{"asin": r["asin"], "roi": r["roi"]} for r in rows]
