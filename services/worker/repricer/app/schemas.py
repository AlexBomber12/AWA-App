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
