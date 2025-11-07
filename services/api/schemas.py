from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

if TYPE_CHECKING:
    from pydantic import BaseModel as BaseStrictModel
else:
    from awa_common.schemas import BaseStrictModel


class RoiRow(BaseStrictModel):
    """Single row returned by the ROI listings endpoint."""

    asin: str = Field(..., description="Amazon ASIN identifier")
    title: str | None = Field(None, description="Product title")
    category: str | None = Field(None, description="Product category as stored in products.category")
    vendor_id: int | None = Field(None, description="Identifier of the vendor supplying the SKU")
    cost: float | None = Field(None, description="Vendor cost in EUR")
    freight: float | None = Field(None, description="Estimated freight cost per unit in EUR")
    fees: float | None = Field(None, description="Aggregated FBA fees in EUR")
    roi_pct: float | None = Field(None, description="Return on investment percentage for the SKU")


class RoiApprovalResponse(BaseStrictModel):
    """Result payload for ROI approval actions."""

    updated: int = Field(..., description="Number of SKUs updated by the approval request")


class StatsKPI(BaseStrictModel):
    """Aggregate ROI KPIs displayed on the stats dashboard."""

    roi_avg: float = Field(..., description="Average ROI percentage across the ROI view")
    products: int = Field(..., description="Count of distinct ASINs considered in the KPI query")
    vendors: int = Field(..., description="Count of vendors found in the ROI view")


class StatsKPIResponse(BaseStrictModel):
    """Wrapper response for KPI aggregates."""

    kpi: StatsKPI


class RoiByVendorItem(BaseStrictModel):
    """Aggregated ROI metrics for a single vendor."""

    vendor: str | None = Field(None, description="Vendor identifier or name as provided by the query")
    roi_avg: float = Field(..., description="Average ROI percentage for the vendor")
    items: int = Field(..., description="Number of SKUs used for the vendor aggregate")


class RoiByVendorResponse(BaseStrictModel):
    """Response for the /stats/roi_by_vendor endpoint."""

    items: list[RoiByVendorItem]
    total_vendors: int


class ReturnsStatsItem(BaseStrictModel):
    """Aggregated returns information for a single ASIN."""

    asin: str
    qty: int = Field(..., description="Total quantity returned for the ASIN")
    refund_amount: float = Field(..., description="Total refund amount issued for the ASIN")


class ReturnsStatsResponse(BaseStrictModel):
    """Response used by the /stats/returns endpoint."""

    items: list[ReturnsStatsItem]
    total_returns: int


class RoiTrendPoint(BaseStrictModel):
    """Monthly ROI trend point."""

    month: str = Field(..., description="Month (YYYY-MM-DD) extracted from ROI snapshots")
    roi_avg: float = Field(..., description="Average ROI for the month")
    items: int = Field(..., description="Number of SKUs that contributed to the month aggregate")


class RoiTrendResponse(BaseStrictModel):
    """Response for the /stats/roi_trend endpoint."""

    points: list[RoiTrendPoint]


class SkuChartPoint(BaseStrictModel):
    """Single point in the SKU price history chart."""

    date: str = Field(..., description="ISO8601 timestamp of the price capture")
    price: float = Field(..., description="Observed Buy Box price at the capture time")


class SkuResponse(BaseStrictModel):
    """Detailed SKU response used by /sku/{asin}."""

    title: str = Field(..., description="Product title from the catalog")
    roi: float = Field(..., description="ROI percentage from the ROI view")
    fees: float = Field(..., description="Fees associated with the SKU")
    chartData: list[SkuChartPoint] = Field(..., description="Historical price series for the SKU")


class SkuApprovalResponse(BaseStrictModel):
    """Response describing the result of approving a SKU."""

    approved: bool = Field(..., description="Flag indicating the SKU was marked as approved")
    changed: int = Field(..., description="Number of rows changed by the approval operation")


__all__ = [
    "RoiRow",
    "RoiApprovalResponse",
    "StatsKPI",
    "StatsKPIResponse",
    "RoiByVendorItem",
    "RoiByVendorResponse",
    "ReturnsStatsItem",
    "ReturnsStatsResponse",
    "RoiTrendPoint",
    "RoiTrendResponse",
    "SkuChartPoint",
    "SkuResponse",
    "SkuApprovalResponse",
]
