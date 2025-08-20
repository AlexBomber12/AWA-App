from __future__ import annotations

import importlib
import os
from types import ModuleType
from typing import Annotated, List, cast

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

# Reuse existing dependencies if present:
try:
    from services.api.dependencies import get_db  # sync
except Exception:  # pragma: no cover - fallback if dependencies missing

    def get_db() -> Session | None:
        return None


try:
    from services.api.security import (
        require_basic_auth,  # dependency that raises on bad creds
    )
except Exception:
    _security = HTTPBasic()

    def require_basic_auth(
        credentials: HTTPBasicCredentials = Depends(_security),
    ) -> None:  # no-op if project already handles auth globally
        return None


# Fallback to repository helper if available
repo: ModuleType | None
try:
    repo = importlib.import_module("services.api.roi_repository")
except Exception:
    repo = None


Asin = Annotated[str, Field(min_length=1, strip_whitespace=True)]


class ScoreRequest(BaseModel):
    asins: List[Asin] = Field(..., description="List of ASINs")


class ScoreItem(BaseModel):
    asin: str
    roi: float | None = None
    vendor: str | None = None
    category: str | None = None
    error: str | None = None


class ScoreResponse(BaseModel):
    items: List[ScoreItem]


router = APIRouter(prefix="/score", tags=["score"])


def _roi_view_name() -> str:
    if repo and hasattr(repo, "_roi_view_name"):
        return cast(str, repo._roi_view_name())
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
                    "roi": (
                        float(row.roi)
                        if getattr(row, "roi", None) is not None
                        else None
                    ),
                }
    items = []
    for asin in body.asins:
        if asin in found:
            items.append(ScoreItem(**found[asin]))
        else:
            items.append(ScoreItem(asin=asin, error="not_found"))
    return ScoreResponse(items=items)
