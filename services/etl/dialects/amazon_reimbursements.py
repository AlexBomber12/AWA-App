from __future__ import annotations

from pandas import DataFrame

from . import normalise_headers

_FIELDS = {
    "asin": ["asin"],
    "reimb_id": ["reimbursement id", "reimb id"],
    "reimb_date": ["reimbursement date", "reimb date"],
    "qty": ["quantity", "qty"],
    "amount": ["amount"],
    "currency": ["currency"],
    "reason_code": ["reason code"],
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
    return "reimbursement id" in cols or "reimb id" in cols
