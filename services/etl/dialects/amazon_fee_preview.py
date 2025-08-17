from __future__ import annotations

import numpy as np
import pandas as pd
from pandas import DataFrame

from . import normalise_headers

SYNONYMS = {
    "asin": ["asin"],
    "sku": ["seller-sku", "sku"],
    "fnsku": ["fnsku"],
    "referral_fee": ["estimated-referral-fee-per-unit", "referral-fee-per-unit"],
    "fulfillment_fee": ["estimated-fulfillment-fee-per-unit", "fulfillment-fee-per-unit"],
    "storage_fee": ["estimated-storage-fee-per-unit", "storage-fee-per-unit"],
    "estimated_fee_total": [
        "estimated-fee-total",
        "total-fulfillment-fee",
        "total-fee",
        "estimated-total-fee",
    ],
    "currency": ["currency", "currency-code"],
    "captured_at": ["captured-at", "report-date"],
}

TARGET_TABLE = "fee_preview_raw"
TARGET_SCHEMA = None
TARGET_COLUMNS = [
    "asin",
    "sku",
    "fnsku",
    "referral_fee",
    "fulfillment_fee",
    "storage_fee",
    "estimated_fee_total",
    "currency",
    "captured_at",
]
CONFLICT_COLS = None


def normalise(df: DataFrame) -> DataFrame:
    lower = {c.lower(): c for c in df.columns}
    for key, options in SYNONYMS.items():
        for opt in options:
            if opt in lower:
                df = df.rename(columns={lower[opt]: key})
                break
    if "captured_at" not in df.columns:
        df["captured_at"] = pd.Timestamp.utcnow()
    for col in TARGET_COLUMNS:
        if col not in df.columns:
            if col in {"referral_fee", "fulfillment_fee", "storage_fee", "estimated_fee_total"}:
                df[col] = pd.Series([np.nan] * len(df), dtype="float64")
            else:
                df[col] = pd.NA
    return df[TARGET_COLUMNS]


def detect(columns: list[str]) -> bool:
    cols = set(normalise_headers(columns))
    has_total = any(opt in cols for opt in SYNONYMS["estimated_fee_total"])
    has_id = any(opt in cols for opt in SYNONYMS["asin"] + SYNONYMS["sku"])
    return has_total and has_id
