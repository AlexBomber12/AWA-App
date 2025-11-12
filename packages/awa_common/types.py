from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TypedDict

from pydantic import Field

from awa_common.schemas import BaseStrictModel


class RateRow(TypedDict):
    carrier: str
    origin: str
    dest: str
    service: str
    eur_per_kg: Decimal
    valid_from: date | None
    valid_to: date | None
    source: str | None


class PriceRow(TypedDict, total=False):
    vendor: str
    sku: str
    unit_price: Decimal
    currency: str
    incoterms: str | None
    pack: int | None
    moq: int | None
    lead_time_d: int | None
    valid_from: date | None
    valid_to: date | None
    source: str | None


class RateRowModel(BaseStrictModel):
    carrier: str = Field(..., min_length=1)
    origin: str = Field(..., min_length=1)
    dest: str = Field(..., min_length=1)
    service: str = Field(..., min_length=1)
    eur_per_kg: Decimal
    valid_from: date | None = None
    valid_to: date | None = None
    source: str | None = None


class PriceRowModel(BaseStrictModel):
    vendor: str | None = None
    sku: str = Field(..., min_length=1)
    unit_price: Decimal
    currency: str = Field(..., min_length=3, max_length=3)
    incoterms: str | None = None
    pack: int | None = None
    moq: int | None = None
    lead_time_d: int | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    source: str | None = None


__all__ = ["RateRow", "PriceRow", "RateRowModel", "PriceRowModel"]
