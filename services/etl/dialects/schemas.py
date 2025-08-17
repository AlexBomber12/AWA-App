from __future__ import annotations

import pandera as pa
from pandera import Check, Column, DataFrameSchema

RETURNS_SCHEMA = DataFrameSchema(
    {
        "asin": Column(pa.String, nullable=False),
        "order_id": Column(pa.String, nullable=True, required=False),
        "return_reason": Column(pa.String, nullable=True, required=False),
        "return_date": Column(pa.DateTime, nullable=False),
        "qty": Column(pa.Int64, Check.ge(0), nullable=False),
        "refund_amount": Column(pa.Float64, nullable=False),
        "currency": Column(pa.String, Check.str_length(3, 3), nullable=False),
    },
    coerce=True,
)

REIMBURSEMENTS_SCHEMA = DataFrameSchema(
    {
        "asin": Column(pa.String, nullable=True, required=False),
        "reimb_id": Column(pa.String, nullable=False),
        "reimb_date": Column(pa.DateTime, nullable=False),
        "qty": Column(pa.Int64, Check.ge(0), nullable=False),
        "amount": Column(pa.Float64, nullable=False),
        "currency": Column(pa.String, Check.str_length(3, 3), nullable=False),
        "reason_code": Column(pa.String, nullable=True, required=False),
    },
    coerce=True,
)


def validate(df, dialect: str):
    if dialect == "returns_report":
        schema = RETURNS_SCHEMA
    elif dialect == "reimbursements_report":
        schema = REIMBURSEMENTS_SCHEMA
    else:
        raise ValueError(f"Unknown dialect: {dialect}")
    return schema.validate(df, lazy=True)
