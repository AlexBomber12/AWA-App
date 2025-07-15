from __future__ import annotations

from pandas import DataFrame

from . import normalise_headers

_FIELDS = {
    "asin": ["asin"],
    "order_id": ["order id", "order_id"],
    "return_reason": ["return reason", "reason"],
    "return_date": ["return date"],
    "qty": ["qty", "quantity"],
    "refund_amount": ["refund amount", "refund"],
    "currency": ["currency"],
}


def normalise(df: DataFrame) -> DataFrame:
    lower = {c.lower(): c for c in df.columns}
    for key, options in _FIELDS.items():
        for opt in options:
            if opt in lower:
                df = df.rename(columns={lower[opt]: key})
                break
    keep = [c for c in _FIELDS.keys() if c in df.columns]
    return df[keep]


def detect(columns: list[str]) -> bool:
    cols = set(normalise_headers(columns))
    return "return reason" in cols or "refund amount" in cols
