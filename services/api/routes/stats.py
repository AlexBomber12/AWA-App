from __future__ import annotations

from fastapi import APIRouter, Depends

try:
    from services.api.security import require_basic_auth
except Exception:
    def require_basic_auth() -> None:
        return None

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/kpi", dependencies=[Depends(require_basic_auth)])
def kpi():
    # Placeholder contract; replace with real aggregates in future PRs
    return {"kpi": {"roi_avg": 0.0, "products": 0, "vendors": 0}}

@router.get("/roi_by_vendor", dependencies=[Depends(require_basic_auth)])
def roi_by_vendor():
    # Placeholder contract; replace with real breakdown
    return {"items": [], "total_vendors": 0}

@router.get("/roi_trend", dependencies=[Depends(require_basic_auth)])
def roi_trend():
    # Placeholder contract; replace with real time series
    return {"points": []}
