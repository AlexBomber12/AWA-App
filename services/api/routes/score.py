from __future__ import annotations

import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, constr
from sqlalchemy import text
from sqlalchemy.orm import Session

# Reuse existing dependencies if present:
try:
    from services.api.dependencies import get_db  # sync
except Exception:  # pragma: no cover - fallback if dependencies missing

    def get_db():
        return None


try:
    from services.api.security import (
        require_basic_auth,  # dependency that raises on bad creds
    )
except Exception:

    def require_basic_auth() -> None:  # no-op if project already handles auth globally
        return None


# Fallback to repository helper if available
try:
    from services.api import roi_repository as repo
except Exception:
    repo = None


class ScoreRequest(BaseModel):
    asins: List[constr(strip_whitespace=True, min_length=1)] = Field(
        ..., description="List of ASINs"
    )


class ScoreItem(BaseModel):
    asin: str
    roi: Optional[float] = None
    vendor: Optional[str] = None
    category: Optional[str] = None
    error: Optional[str] = None


class ScoreResponse(BaseModel):
    items: List[ScoreItem]


router = APIRouter(prefix="/score", tags=["score"])


def _roi_view_name() -> str:
    if repo and hasattr(repo, "_roi_view_name"):
        return repo._roi_view_name()
    return os.getenv("ROI_VIEW_NAME", "v_roi_full")


@router.post(
    "", response_model=ScoreResponse, dependencies=[Depends(require_basic_auth)]
)
def score(body: ScoreRequest, db: Session | None = Depends(get_db)) -> ScoreResponse:
    if not body.asins:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="asins must be a non-empty list",
        )

    view = _roi_view_name()
    found = {}
    if db is not None:
        for asin in body.asins:
            row = db.execute(
                text(
                    f"SELECT asin, vendor, category, roi FROM {view} WHERE asin = :asin"
                ),
                {"asin": asin},
            ).fetchone()
            if row:
                found[row.asin] = {
                    "asin": row.asin,
                    "vendor": getattr(row, "vendor", None),
                    "category": getattr(row, "category", None),
                    "roi": float(row.roi)
                    if getattr(row, "roi", None) is not None
                    else None,
                }
    items = []
    for asin in body.asins:
        if asin in found:
            items.append(ScoreItem(**found[asin]))
        else:
            items.append(ScoreItem(asin=asin, error="not_found"))
    return ScoreResponse(items=items)
