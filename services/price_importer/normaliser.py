from __future__ import annotations

from collections.abc import Mapping
from difflib import get_close_matches

import pandas as pd

_FIELD_MAP = {
    "sku": ["sku", "asin", "code"],
    "cost": ["cost", "unit cost", "price eur", "price", "fob"],
    "moq": ["moq", "minimum order", "min qty"],
    "lead_time_days": ["lead time", "leadtime", "lead"],
    "currency": ["currency", "curr"],
}


def guess_columns(df: pd.DataFrame) -> dict[str, str]:
    lower = {c.lower(): c for c in df.columns}
    mapping: dict[str, str] = {}
    for key, options in _FIELD_MAP.items():
        for opt in options:
            match = get_close_matches(opt, lower.keys(), n=1, cutoff=0.6)
            if match:
                mapping[key] = lower[match[0]]
                break
    return mapping


def normalise(df: pd.DataFrame, mapping: Mapping[str, str] | None = None) -> pd.DataFrame:
    """Normalise vendor price frames using heuristic and optional LLM mapping."""

    cols = guess_columns(df)
    if mapping:
        mapping_lower = {k: str(v).strip().lower() for k, v in mapping.items() if v is not None}
        resolved: dict[str, str] = {}
        lower_cols = {c.lower(): c for c in df.columns}
        for target, source in mapping_lower.items():
            col_name = lower_cols.get(source)
            if col_name:
                resolved[target] = col_name
        if resolved:
            cols.update(resolved)
    df = df.rename(columns={v: k for k, v in cols.items() if v in df.columns})
    keep = [c for c in ["sku", "cost", "moq", "lead_time_days", "currency"] if c in df.columns]
    return df[keep]
