from typing import List
import asyncpg
import aiosqlite
from fastapi import FastAPI
from db import pg_dsn


app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
async def startup():
    dsn = pg_dsn()
    if dsn.startswith("sqlite"):
        path = dsn.replace("sqlite:///", "")
        app.state.db = await aiosqlite.connect(path)
        app.state.kind = "sqlite"
    else:
        app.state.db = await asyncpg.create_pool(dsn)
        app.state.kind = "pg"


@app.on_event("shutdown")
async def shutdown():
    if app.state.kind == "sqlite":
        await app.state.db.close()
    else:
        await app.state.db.close()


@app.post("/score")
async def score(asins: List[str]):
    query = """
        SELECT p.asin, (p.price - o.cost) / o.cost AS roi
        FROM product p
        JOIN offers o ON p.asin = o.asin
        WHERE p.asin = ANY($1::text[])
        ORDER BY roi DESC
    """
    if app.state.kind == "sqlite":
        placeholders = ",".join("?" for _ in asins)
        q = query.replace("p.asin = ANY($1::text[])", f"p.asin IN ({placeholders})")
        async with app.state.db.execute(q, asins) as cur:
            rows = await cur.fetchall()
        return [{"asin": r[0], "roi": r[1]} for r in rows]
    rows = await app.state.db.fetch(query, asins)
    return [{"asin": r["asin"], "roi": r["roi"]} for r in rows]
