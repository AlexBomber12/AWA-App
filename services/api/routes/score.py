from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

if TYPE_CHECKING:
    from pydantic import BaseModel as BaseStrictModel
else:
    from awa_common.schemas import BaseStrictModel

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BeforeValidator, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.api.roi_views import InvalidROIViewError, get_roi_view_name, quote_identifier

# Reuse existing dependencies if present:
try:
    from services.api.dependencies import get_db  # sync
except Exception:  # pragma: no cover - fallback if dependencies missing

    def get_db() -> Session | None:
        return None


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


def _roi_view_name() -> str:
    return get_roi_view_name()


def _quoted_roi_view() -> str:
    return quote_identifier(_roi_view_name())


@router.post(
    "",
    response_model=ScoreResponse,
    dependencies=[Depends(require_viewer), Depends(limit_viewer)],
)
def score(body: ScoreRequest, db: Session | None = Depends(get_db)) -> ScoreResponse:
    if not body.asins:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="asins must be a non-empty list",
        )

    try:
        view_identifier = _quoted_roi_view()
    except InvalidROIViewError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    stmt = text(f"SELECT asin, vendor, category, roi FROM {view_identifier} WHERE asin = :asin")
    found = {}
    if db is not None:
        for asin in body.asins:
            row = db.execute(stmt, {"asin": asin}).fetchone()
            if row:
                found[row.asin] = {
                    "asin": row.asin,
                    "vendor": getattr(row, "vendor", None),
                    "category": getattr(row, "category", None),
                    "roi": (float(row.roi) if getattr(row, "roi", None) is not None else None),
                }
    items = []
    for asin in body.asins:
        if asin in found:
            items.append(ScoreItem(**found[asin]))
        else:
            items.append(ScoreItem(asin=asin, error="not_found"))
    return ScoreResponse(items=items)
