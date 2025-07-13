from fastapi import APIRouter

router = APIRouter()


@router.get("/stats/kpi")
def kpi():
    """Return KPI metrics (mock)."""
    # TODO: replace with SQL queries
    return [
        {"name": "Total SKU", "value": 10},
        {"name": "Avg ROI %", "value": 12},
        {"name": "Approved €", "value": 1000},
        {"name": "Potential Profit €", "value": 2000},
    ]


@router.get("/stats/roi_by_vendor")
def roi_by_vendor():
    """Return ROI percent by vendor."""
    # TODO: replace with SQL queries
    return [{"vendor": "ACME", "roi": 15}]


@router.get("/stats/roi_trend")
def roi_trend():
    """Return 30-day ROI trend."""
    # TODO: replace with SQL queries
    return [{"date": "2024-01-01", "roi": 10}]
