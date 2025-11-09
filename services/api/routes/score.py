from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

if TYPE_CHECKING:
    from pydantic import BaseModel as BaseStrictModel
else:
    from awa_common.schemas import BaseStrictModel

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BeforeValidator, Field
from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from awa_common.db.async_session import get_async_session
from awa_common.roi_views import InvalidROIViewError, current_roi_view, quote_identifier
from services.api.security import limit_viewer, require_viewer


def _strip_asin(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("ASIN must be provided as a string.")
    return value.strip()


Asin = Annotated[str, BeforeValidator(_strip_asin), Field(min_length=1)]


class ScoreRequest(BaseStrictModel):
    asins: list[Asin] = Field(..., description="List of ASINs")


class ScoreItem(BaseStrictModel):
    asin: str
    roi: float | None = None
    vendor: str | None = None
    category: str | None = None
    error: str | None = None


class ScoreResponse(BaseStrictModel):
    items: list[ScoreItem]


router = APIRouter(prefix="/score", tags=["score"])


@router.post(
    "",
    response_model=ScoreResponse,
    dependencies=[Depends(require_viewer), Depends(limit_viewer)],
)
async def score(
    body: ScoreRequest,
    session: AsyncSession = Depends(get_async_session),
) -> ScoreResponse:
    if not body.asins:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="asins must be a non-empty list",
        )

    try:
        view_identifier = quote_identifier(current_roi_view())
    except InvalidROIViewError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    stmt = text(
        f"""
            SELECT asin, vendor, category, roi
              FROM {view_identifier}
             WHERE asin IN :asins
            """
    ).bindparams(bindparam("asins", expanding=True))
    result = await session.execute(stmt, {"asins": tuple(body.asins)})
    found = {
        row.asin: ScoreItem(
            asin=row.asin,
            vendor=getattr(row, "vendor", None),
            category=getattr(row, "category", None),
            roi=float(row.roi) if getattr(row, "roi", None) is not None else None,
        )
        for row in result
    }
    items = [found.get(asin, ScoreItem(asin=asin, error="not_found")) for asin in body.asins]
    return ScoreResponse(items=items)
