import asyncio
from contextlib import asynccontextmanager
from typing import List

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Depends, FastAPI  # type: ignore[attr-defined]

from .routes.roi import router as roi_router
from .routes.stats import router as stats_router

from .db import get_session
from services.common.dsn import build_dsn


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _wait_for_db()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(roi_router)
app.include_router(stats_router)


async def _wait_for_db() -> None:
    """Block application startup until the database becomes available."""
    from sqlalchemy import create_engine

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


@app.get("/health")
async def health(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    await session.execute(text("SELECT 1 FROM v_roi_full LIMIT 1"))
    return {"db": "ok"}


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
