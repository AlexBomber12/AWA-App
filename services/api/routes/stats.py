from __future__ import annotations

import os
from fastapi import APIRouter, Depends
from sqlalchemy import text

try:
    from services.api.dependencies import get_db
except Exception:
    get_db = None
try:
    from services.api.security import require_basic_auth
except Exception:
    require_basic_auth = lambda: None
try:
    from services.api import roi_repository as repo
except Exception:
    repo = None

router = APIRouter(prefix="/stats", tags=["stats"])


def _roi_view_name():
    if repo and hasattr(repo, "_roi_view_name"):
        return repo._roi_view_name()
    return os.getenv("ROI_VIEW_NAME", "v_roi_full")


@router.get("/kpi", dependencies=[Depends(require_basic_auth)])
def kpi(db=Depends(get_db) if get_db else None):
    if os.getenv("STATS_USE_SQL") == "1" and db is not None:
        view = _roi_view_name()
        row = db.execute(
            text(
                f"SELECT AVG(roi) AS roi_avg, COUNT(DISTINCT asin) AS products, COUNT(DISTINCT vendor) AS vendors FROM {view}"
            )
        ).mappings().first()
        return {
            "kpi": {
                "roi_avg": float(row.get("roi_avg") or 0.0),
                "products": int(row.get("products") or 0),
                "vendors": int(row.get("vendors") or 0),
            }
        }
    return {"kpi": {"roi_avg": 0.0, "products": 0, "vendors": 0}}


@router.get("/roi_by_vendor", dependencies=[Depends(require_basic_auth)])
def roi_by_vendor(db=Depends(get_db) if get_db else None):
    if os.getenv("STATS_USE_SQL") == "1" and db is not None:
        view = _roi_view_name()
        rows = db.execute(
            text(
                f"SELECT vendor, AVG(roi) AS roi_avg, COUNT(*) AS items FROM {view} GROUP BY vendor ORDER BY vendor"
            )
        ).mappings().all()
        return {
            "items": [
                {
                    "vendor": r["vendor"],
                    "roi_avg": float(r.get("roi_avg") or 0.0),
                    "items": int(r.get("items") or 0),
                }
                for r in rows
            ],
            "total_vendors": len(rows),
        }
    return {"items": [], "total_vendors": 0}


@router.get("/roi_trend", dependencies=[Depends(require_basic_auth)])
def roi_trend(db=Depends(get_db) if get_db else None):
    if os.getenv("STATS_USE_SQL") == "1" and db is not None:
        view = _roi_view_name()
        for date_col in ("dt", "date", "snapshot_date", "created_at"):
            try:
                rows = db.execute(
                    text(
                        f"SELECT date_trunc('month', {date_col})::date AS month, AVG(roi) AS roi_avg, COUNT(*) AS items FROM {view} GROUP BY 1 ORDER BY 1"
                    )
                ).mappings().all()
                if rows:
                    return {
                        "points": [
                            {
                                "month": str(r["month"]),
                                "roi_avg": float(r.get("roi_avg") or 0.0),
                                "items": int(r.get("items") or 0),
                            }
                            for r in rows
                        ]
                    }
            except Exception:
                continue
        return {"points": []}
    return {"points": []}
