from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from awa_common.db.async_session import get_async_session

MAX_SKEW = 30  # seconds

router = APIRouter()


@router.get("/health", include_in_schema=False)  # type: ignore[misc]
async def health(session: AsyncSession = Depends(get_async_session)) -> JSONResponse:
    """Return 200 when DB reachable and clocks are in sync."""
    result = await session.execute(text("SELECT (now() AT TIME ZONE 'UTC')"))
    db_now = result.scalar()
    if isinstance(db_now, datetime):
        db_now = db_now.replace(tzinfo=UTC)
    app_now = datetime.now(UTC)
    if db_now is None or abs((db_now - app_now).total_seconds()) > MAX_SKEW:
        return JSONResponse(status_code=503, content={"detail": "clock_skew"})
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok"})
