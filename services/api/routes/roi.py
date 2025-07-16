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
from sqlalchemy import String, bindparam, create_engine, text
from sqlalchemy.types import Numeric

from services.common.dsn import build_dsn

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


def build_pending_sql(include_vendor: bool, include_category: bool):
    base = """
        SELECT p.asin, p.title, p.category,
               vp.vendor_id, vp.cost,
               (p.weight_kg * fr.eur_per_kg) AS freight,
               (f.fulfil_fee + f.referral_fee + f.storage_fee) AS fees,
               vf.roi_pct
        FROM v_roi_full vf
        JOIN products p   ON p.asin = vf.asin
        JOIN vendor_prices vp ON vp.sku = p.asin
        JOIN freight_rates fr ON fr.lane = 'EU→IT' AND fr.mode = 'sea'
        JOIN fees_raw f  ON f.asin = p.asin
        WHERE vf.roi_pct >= :roi_min
          AND COALESCE(p.status, 'pending') = 'pending'
    """
    params = [bindparam("roi_min", type_=Numeric)]
    if include_vendor:
        base += " AND vp.vendor_id = :vendor"
        params.append(bindparam("vendor", type_=String))
    if include_category:
        base += " AND p.category   = :category"
        params.append(bindparam("category", type_=String))
    base += " LIMIT 200"
    return text(base).bindparams(*params)


@router.get("/roi-review")
def roi_review(
    request: Request,
    roi_min: int = 0,
    vendor: Optional[int] = None,
    category: Optional[str] = None,
    _: str = Depends(_check_basic_auth),
):
    url = build_dsn(sync=True)
    engine = create_engine(url)
    stmt = build_pending_sql(vendor is not None, category is not None)
    params = {"roi_min": roi_min}
    if vendor is not None:
        params["vendor"] = vendor
    if category is not None:
        params["category"] = category
    with engine.connect() as conn:
        res = conn.execute(stmt, params)
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


APPROVE_SQL = text(
    """
    UPDATE products
       SET status = 'approved'
     WHERE asin = ANY(:asins)
       AND COALESCE(status,'pending') = 'pending'
     RETURNING asin
    """
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
        return {"updated": 0}
    url = build_dsn(sync=True)
    engine = create_engine(url)
    with engine.begin() as conn:
        rows = conn.execute(APPROVE_SQL, {"asins": asins}).scalars().all()
        count = len(rows)
    engine.dispose()
    return {"updated": count}
