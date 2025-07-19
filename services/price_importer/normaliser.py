from __future__ import annotations

from difflib import get_close_matches
from typing import Mapping

import pandas as pd

_FIELD_MAP = {
    "sku": ["sku", "asin", "code"],
    "cost": ["cost", "unit cost", "price eur", "price", "fob"],
    "moq": ["moq", "minimum order", "min qty"],
    "lead_time_days": ["lead time", "leadtime", "lead"],
    "currency": ["currency", "curr"],
}


def guess_columns(df: pd.DataFrame) -> Mapping[str, str]:
    lower = {c.lower(): c for c in df.columns}
    mapping: dict[str, str] = {}
    for key, options in _FIELD_MAP.items():
        for opt in options:
            match = get_close_matches(opt, lower.keys(), n=1, cutoff=0.6)
            if match:
                mapping[key] = lower[match[0]]
                break
    return mapping


def normalise(df: pd.DataFrame) -> pd.DataFrame:
    cols = guess_columns(df)
    df = df.rename(columns={v: k for k, v in cols.items()})
    keep = [
        c
        for c in ["sku", "cost", "moq", "lead_time_days", "currency"]
        if c in df.columns
    ]
    return df[keep]
