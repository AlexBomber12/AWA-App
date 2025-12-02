from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Any, Literal

from pydantic import Field

if TYPE_CHECKING:
    from pydantic import BaseModel as BaseStrictModel
else:
    from awa_common.schemas import BaseStrictModel

ErrorCode = Literal[
    "unsupported_file_format",
    "bad_request",
    "unprocessable_entity",
    "validation_error",
    "payload_too_large",
]


class ErrorDetail(BaseStrictModel):
    code: ErrorCode | str = Field(..., description="Machine-readable error code")
    detail: str = Field(..., description="Human-readable description of the error")
    hint: str | None = Field(None, description="Optional recovery guidance")


class ErrorResponse(BaseStrictModel):
    """Standard error payload returned by ETL ingest routes."""

    error: ErrorDetail = Field(..., description="Structured error object")
    request_id: str = Field(..., description="Correlation identifier echoed from the request")


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


class PaginationMeta(BaseStrictModel):
    """Common pagination envelope returned by list endpoints."""

    page: int = Field(..., description="Current 1-based page number")
    page_size: int = Field(..., description="Configured page size")
    total: int = Field(..., description="Total number of rows that match the filters")
    total_pages: int = Field(..., description="Total pages derived from the total and page size")


class RoiListResponse(BaseStrictModel):
    """Paginated ROI response returned by /roi."""

    items: list[RoiRow]
    pagination: PaginationMeta


class RoiApprovalResponse(BaseStrictModel):
    """Result payload for ROI approval actions."""

    updated: int = Field(..., description="Number of SKUs updated by the approval request")
    approved_ids: list[str] = Field(default_factory=list, description="Identifiers that were approved in this request")


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


class ReturnsSummary(BaseStrictModel):
    """Aggregate metrics used by the returns table summary widgets."""

    total_asins: int = Field(..., description="Total ASINs that matched the filters")
    total_units: int = Field(..., description="Total quantity of units returned for the filters")
    total_refund_amount: float = Field(..., description="Total refund amount issued for the filters")
    avg_refund_per_unit: float = Field(..., description="Average refund per returned unit")
    top_asin: str | None = Field(None, description="ASIN with the highest refund amount for the filters")
    top_refund_amount: float | None = Field(
        None, description="Refund amount associated with the ASIN that ranked first"
    )


class ReturnsStatsResponse(BaseStrictModel):
    """Response used by the /stats/returns endpoint."""

    items: list[ReturnsStatsItem]
    total_returns: int
    pagination: PaginationMeta
    summary: ReturnsSummary


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


class DecisionReason(BaseStrictModel):
    code: str
    message: str
    data: dict[str, Any] | None = None
    metric: str | None = None


class DecisionAlternative(BaseStrictModel):
    action: str
    label: str | None = None
    impact: str | None = None
    confidence: float | None = None
    why: list[DecisionReason] = Field(default_factory=list)


class DecisionLinks(BaseStrictModel):
    asin: str | None = None
    vendor_id: int | None = None
    thread_id: str | None = None
    entity_type: str | None = None
    campaign_id: int | None = None
    price_list_row_id: str | None = None
    entity_id: str | None = None
    category: str | None = None


class DecisionTask(BaseStrictModel):
    id: str
    source: str
    entity: dict[str, Any]
    decision: str
    priority: int
    status: str
    deadline_at: dt.datetime | None = None
    default_action: str | None = None
    why: list[DecisionReason] = Field(default_factory=list)
    alternatives: list[DecisionAlternative] = Field(default_factory=list)
    next_request_at: dt.datetime | None = None
    state: str | None = None
    assignee: str | None = None
    summary: str | None = None
    metrics: dict[str, Any] | None = None
    links: DecisionLinks = Field(default_factory=DecisionLinks)
    created_at: dt.datetime | None = None
    updated_at: dt.datetime | None = None


class DecisionTaskSummary(BaseStrictModel):
    pending: int = 0
    applied: int = 0
    dismissed: int = 0
    expired: int = 0
    snoozed: int = 0
    open: int = 0
    in_progress: int = 0
    blocked: int = 0


class DecisionTaskListResponse(BaseStrictModel):
    items: list[DecisionTask]
    pagination: PaginationMeta
    summary: DecisionTaskSummary | None = None


class TaskUpdateRequest(BaseStrictModel):
    state: Literal["pending", "snoozed", "applied", "dismissed", "expired"] | None = None
    assignee: str | None = None
    note: str | None = None
    next_request_at: dt.datetime | None = None


class DecisionPreviewResponse(BaseStrictModel):
    planned: list[DecisionTask]
    generated: int
    candidates: int


__all__ = [
    "ErrorCode",
    "ErrorResponse",
    "RoiRow",
    "PaginationMeta",
    "RoiListResponse",
    "RoiApprovalResponse",
    "StatsKPI",
    "StatsKPIResponse",
    "RoiByVendorItem",
    "RoiByVendorResponse",
    "ReturnsStatsItem",
    "ReturnsStatsResponse",
    "ReturnsSummary",
    "RoiTrendPoint",
    "RoiTrendResponse",
    "SkuChartPoint",
    "SkuResponse",
    "SkuApprovalResponse",
    "DecisionAlternative",
    "DecisionLinks",
    "DecisionPreviewResponse",
    "DecisionReason",
    "DecisionTask",
    "DecisionTaskListResponse",
    "DecisionTaskSummary",
    "TaskUpdateRequest",
]
