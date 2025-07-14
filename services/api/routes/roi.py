from __future__ import annotations

import os
import secrets
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from starlette import status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text, bindparam

from services.common.db_url import build_url

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


ROI_SQL = text(
    """
        SELECT p.asin, p.title, p.category,
               vp.vendor_id, vp.cost,
               (p.weight_kg * fr.eur_per_kg) AS freight,
               (f.fulfil_fee + f.referral_fee + f.storage_fee) AS fees,
               vf.roi_pct
        FROM v_roi_full vf
        JOIN products p   ON p.asin = vf.asin
        JOIN vendor_prices vp ON vp.sku = p.asin
        JOIN freight_rates fr ON fr.lane='EU→IT' AND fr.mode='sea'
        JOIN fees_raw f  ON f.asin = p.asin
        WHERE vf.roi_pct >= :roi_min
          AND COALESCE(p.status, 'pending') = 'pending'
          AND (:vendor IS NULL OR vp.vendor_id = :vendor)
          AND (:category IS NULL OR p.category = :category)
        LIMIT 200
        """
).bindparams(
    bindparam("roi_min"),
    bindparam("vendor"),
    bindparam("category"),
)


@router.get("/roi-review")
def roi_review(
    request: Request,
    roi_min: int = 0,
    vendor: Optional[int] = None,
    category: Optional[str] = None,
    _: str = Depends(_check_basic_auth),
):
    url = build_url(async_=False)
    engine = create_engine(url)
    with engine.connect() as conn:
        res = conn.execute(ROI_SQL, {"roi_min": roi_min, "vendor": vendor, "category": category})
        items = [dict(row._mapping) for row in res.fetchall()]
    engine.dispose()
    context = {
        "request": request,
        "items": items,
        "rows": items,
        "roi_min": roi_min,
        "vendor": vendor,
        "category": category,
    }
    return templates.TemplateResponse("roi_review.html", context)


UPDATE_SQL = text(
    "UPDATE products SET status='approved'"
    " WHERE asin IN :asins AND COALESCE(status, 'pending') = 'pending'"
).bindparams(bindparam("asins", expanding=True))


async def _extract_asins(request: Request) -> List[str]:
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
        return data.get("asins", [])
    form = await request.form()
    values = form.getlist("asins")
    return [str(value) for value in values]


@router.post("/roi-review/approve")
async def approve(request: Request, _: str = Depends(_check_basic_auth)) -> dict[str, int]:
    asins = await _extract_asins(request)
    if not asins:
        return {"count": 0}
    url = build_url(async_=False)
    engine = create_engine(url)
    with engine.begin() as conn:
        res = conn.execute(UPDATE_SQL, {"asins": asins})
        count = res.rowcount or 0
    engine.dispose()
    return {"count": count}
