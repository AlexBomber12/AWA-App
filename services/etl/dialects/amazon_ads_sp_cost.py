from __future__ import annotations

import numpy as np
import pandas as pd
from pandas import DataFrame

from . import normalise_headers

SYNONYMS = {
    "date": ["date"],
    "campaign_id": ["campaign-id"],
    "ad_group_id": ["ad-group-id"],
    "keyword_id": ["keyword-id"],
    "targeting": ["targeting"],
    "impressions": ["impressions"],
    "clicks": ["clicks"],
    "spend": ["spend"],
    "orders": ["orders"],
    "sales": ["sales"],
    "currency": ["currency", "currency-code"],
}

TARGET_TABLE = "ads_sp_cost_daily_raw"
TARGET_SCHEMA = None
TARGET_COLUMNS = [
    "date",
    "campaign_id",
    "ad_group_id",
    "keyword_id",
    "targeting",
    "impressions",
    "clicks",
    "spend",
    "orders",
    "sales",
    "currency",
]
CONFLICT_COLS = ("date", "campaign_id", "ad_group_id", "keyword_id")


def normalise(df: DataFrame) -> DataFrame:
    lower = {c.lower(): c for c in df.columns}
    for key, options in SYNONYMS.items():
        for opt in options:
            if opt in lower:
                df = df.rename(columns={lower[opt]: key})
                break
    for col in TARGET_COLUMNS:
        if col not in df.columns:
            if col in {"impressions", "clicks"}:
                df[col] = pd.Series([0] * len(df), dtype="Int64")
            elif col == "orders":
                df[col] = pd.Series([0] * len(df), dtype="Int64")
            elif col in {"spend", "sales"}:
                df[col] = pd.Series([np.nan] * len(df), dtype="float64")
            else:
                df[col] = pd.NA
    return df[TARGET_COLUMNS]


def detect(columns: list[str]) -> bool:
    cols = set(normalise_headers(columns))
    required = ["campaign-id", "ad-group-id", "impressions", "clicks", "spend", "date"]
    return all(c in cols for c in required)
