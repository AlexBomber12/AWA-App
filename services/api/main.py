from typing import List
from fastapi import FastAPI
import asyncpg
import os


def pg_dsn() -> str:
    if "DATABASE_URL" in os.environ:
        return os.environ["DATABASE_URL"]
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "pass")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "postgres")
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
async def startup():
    app.state.pool = await asyncpg.create_pool(pg_dsn())


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
