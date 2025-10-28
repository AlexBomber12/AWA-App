from decimal import Decimal

from pydantic import BaseModel, Field


class PriceRequest(BaseModel):
    asin: str = Field(..., min_length=10, max_length=14)
    our_cost: Decimal = Field(..., gt=0)
    fee_estimate: Decimal = Field(..., ge=0)


class PriceResponse(BaseModel):
    asin: str
    new_price: Decimal
    rule_applied: str = "baseline"


class SimItem(BaseModel):
    asin: str = Field(..., min_length=10, max_length=14)
    map_price: Decimal | None = None


class SimulateRequest(BaseModel):
    asin: str | None = None
    items: list[SimItem] | None = None


class SimulateResult(BaseModel):
    asin: str
    new_price: Decimal
    strategy: str
    context: dict


class SimulateResponse(BaseModel):
    results: list[SimulateResult]


class ApplyItem(BaseModel):
    asin: str = Field(..., min_length=10, max_length=14)
    new_price: Decimal
    strategy: str
    old_price: Decimal | None = None
    note: str | None = None
    map_price: Decimal | None = None


class ApplyRequest(BaseModel):
    items: list[ApplyItem]
    dry_run: bool = False


class ApplyResponse(BaseModel):
    applied: int
    results: list[dict]
