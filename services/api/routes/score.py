from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

if TYPE_CHECKING:
    from pydantic import BaseModel as BaseStrictModel
else:
    from awa_common.schemas import BaseStrictModel

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BeforeValidator, Field
from sqlalchemy.ext.asyncio import AsyncSession

from awa_common.db.async_session import get_async_session
from services.api import roi_repository
from services.api.rate_limit import score_rate_limiter
from services.api.roi_views import InvalidROIViewError, get_roi_view_name
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
    dependencies=[Depends(require_viewer), Depends(limit_viewer), Depends(score_rate_limiter())],
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
        roi_view = get_roi_view_name()
    except InvalidROIViewError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    rows_by_asin = await roi_repository.fetch_scores_for_asins(session, body.asins, roi_view)
    items: list[ScoreItem] = []
    for asin in body.asins:
        row = rows_by_asin.get(asin)
        if not row:
            items.append(ScoreItem(asin=asin, error="not_found"))
            continue
        roi_value = row.get("roi")
        try:
            roi = float(roi_value) if roi_value is not None else None
        except (TypeError, ValueError):
            roi = None
        items.append(
            ScoreItem(
                asin=asin,
                vendor=row.get("vendor"),
                category=row.get("category"),
                roi=roi,
            )
        )
    return ScoreResponse(items=items)
