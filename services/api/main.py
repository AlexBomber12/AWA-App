from typing import List
import asyncpg
import aiosqlite
from fastapi import FastAPI
import os
import pathlib

# --------------------------------------------------------------------------- #
# Database URL fallback logic
# --------------------------------------------------------------------------- #

_DEFAULT_DB_URL = "sqlite+aiosqlite:///data/awa.db"

# If running **outside** the container (CI unit-tests) we usually cannot
# create /data.  Fall back to a project-local file.
if not os.access("/data", os.W_OK):
    _DEFAULT_DB_URL = "sqlite+aiosqlite:///./awa.db"
else:  # container path – make sure the dir exists
    try:
        pathlib.Path("/data").mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # very unlikely inside Docker, but keep CI green
        _DEFAULT_DB_URL = "sqlite+aiosqlite:///./awa.db"

# Allow override via env, otherwise use computed default
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_DB_URL)
# propagate default to env for other modules
os.environ.setdefault("DATABASE_URL", DATABASE_URL)


app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
async def startup():
    dsn = DATABASE_URL
    if dsn.startswith("sqlite"):
        path = dsn.replace("sqlite:///", "").replace("sqlite+aiosqlite:///", "")
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
