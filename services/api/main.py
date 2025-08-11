import asyncio
import os
from contextlib import asynccontextmanager
from typing import List

import httpx
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from alembic.config import Config
from alembic.script import ScriptDirectory
from services.common.dsn import build_dsn
from services.ingest.ingest_router import router as ingest_router
from services.ingest.upload_router import router as upload_router

from .db import get_session
from .routes import health as health_router
from .routes.roi import router as roi_router
from .routes.stats import router as stats_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _wait_for_db()
    await _check_llm()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/ready", status_code=status.HTTP_200_OK, include_in_schema=False)
async def ready(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    """Return 200 only when migrations are at head."""
    alembic_config = os.getenv("ALEMBIC_CONFIG", "alembic.ini")
    cfg = Config(alembic_config)
    head = ScriptDirectory.from_config(cfg).get_current_head()
    result = await session.execute(text("SELECT version_num FROM alembic_version"))
    current = result.scalar()
    if current == head:
        return {"status": "ready"}
    raise HTTPException(status_code=503, detail="migrations pending")


app.include_router(upload_router, prefix="/upload")
app.include_router(ingest_router)
app.include_router(roi_router)
app.include_router(stats_router)
app.include_router(health_router.router)


async def _wait_for_db() -> None:
    """Block application startup until the database becomes available."""
    from sqlalchemy import create_engine

    # Use DATABASE_URL if set, otherwise build sync DSN
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Convert async URL to sync URL
        url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    else:
        url = build_dsn(sync=True)
    
    delay = 0.2
    for _ in range(10):
        try:
            engine = create_engine(url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine.dispose()
            return
        except Exception:
            await asyncio.sleep(delay)
    raise RuntimeError("Database not available")


async def _check_llm() -> None:
    from services.common.llm import LAN_BASE, LLM_PROVIDER, LLM_PROVIDER_FALLBACK

    if LLM_PROVIDER != "lan":
        return
    try:
        async with httpx.AsyncClient(timeout=5) as cli:
            await cli.get(f"{LAN_BASE}/health")
    except Exception:
        os.environ["LLM_PROVIDER"] = LLM_PROVIDER_FALLBACK


@app.post("/score")
async def score(
    asins: List[str], session: AsyncSession = Depends(get_session)
) -> list[dict[str, float | str]]:
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
