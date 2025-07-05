from __future__ import annotations

import os
import secrets
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Form,
)
from starlette import status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from .repository import fetch_roi_rows, bulk_approve

router = APIRouter()
security = HTTPBasic()
templates = Jinja2Templates(directory="templates")


def _check_basic_auth(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    user = os.getenv("BASIC_USER", "admin")
    pwd = os.getenv("BASIC_PASS", "pass")
    ok = secrets.compare_digest(credentials.username, user) and secrets.compare_digest(
        credentials.password, pwd
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@router.get("/roi-review")
async def roi_review(
    request: Request,
    roi_min: float = 0,
    vendor: Optional[str] = None,
    category: Optional[str] = None,
    _: str = Depends(_check_basic_auth),
    session: AsyncSession = Depends(get_session),
):
    rows = await fetch_roi_rows(session, roi_min, vendor, category)
    context = {
        "request": request,
        "rows": rows,
        "roi_min": roi_min,
        "vendor": vendor,
        "category": category,
    }
    return templates.TemplateResponse("roi_review.html", context)


@router.post("/roi-review/approve")
async def approve(
    asins: List[str] = Form(...),
    _: str = Depends(_check_basic_auth),
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    count = await bulk_approve(session, asins)
    return {"count": count}
