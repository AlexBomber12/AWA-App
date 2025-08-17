from __future__ import annotations

import os
from datetime import datetime

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from services.ingest.copy_loader import copy_df_via_temp

TEST_DSN = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(TEST_DSN is None, reason="TEST_DATABASE_URL not set")


@pytest.fixture(scope="module")
def engine():
    engine = create_engine(TEST_DSN)
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS test_ingest"))
        conn.execute(
            text("DROP TABLE IF EXISTS test_ingest.reimbursements_raw CASCADE")
        )
        conn.execute(
            text(
                """
                CREATE TABLE test_ingest.reimbursements_raw(
                    reimb_id text PRIMARY KEY,
                    reimb_date timestamp,
                    qty int,
                    amount double precision,
                    currency text,
                    asin text
                )
                """
            )
        )
        conn.execute(text("DROP TABLE IF EXISTS test_ingest.returns_raw CASCADE"))
        conn.execute(
            text(
                """
                CREATE TABLE test_ingest.returns_raw(
                    asin text,
                    return_date timestamp,
                    qty int,
                    refund_amount double precision,
                    currency text
                )
                """
            )
        )
    yield engine
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS test_ingest CASCADE"))
    engine.dispose()


def test_upsert(engine):
    cols = ["reimb_id", "reimb_date", "qty", "amount", "currency", "asin"]
    df1 = pd.DataFrame(
        [
            {
                "reimb_id": "r1",
                "reimb_date": datetime(2024, 1, 1),
                "qty": 1,
                "amount": 10.0,
                "currency": "USD",
                "asin": "A",
            },
            {
                "reimb_id": "r2",
                "reimb_date": datetime(2024, 1, 2),
                "qty": 2,
                "amount": 20.0,
                "currency": "USD",
                "asin": "B",
            },
        ]
    )
    copy_df_via_temp(
        engine,
        df1,
        target_table="reimbursements_raw",
        target_schema="test_ingest",
        columns=cols,
        conflict_cols=("reimb_id",),
    )

    df2 = pd.DataFrame(
        [
            {
                "reimb_id": "r1",
                "reimb_date": datetime(2024, 1, 1),
                "qty": 1,
                "amount": 30.0,
                "currency": "USD",
                "asin": "A",
            },
            {
                "reimb_id": "r2",
                "reimb_date": datetime(2024, 1, 2),
                "qty": 2,
                "amount": 20.0,
                "currency": "USD",
                "asin": "B",
            },
        ]
    )
    copy_df_via_temp(
        engine,
        df2,
        target_table="reimbursements_raw",
        target_schema="test_ingest",
        columns=cols,
        conflict_cols=("reimb_id",),
    )

    with engine.connect() as conn:
        cnt = conn.execute(
            text("SELECT count(*) FROM test_ingest.reimbursements_raw")
        ).scalar()
        amt = conn.execute(
            text(
                "SELECT amount FROM test_ingest.reimbursements_raw WHERE reimb_id='r1'"
            )
        ).scalar()
    assert cnt == 2
    assert amt == 30.0


def test_append_only(engine):
    cols = ["asin", "return_date", "qty", "refund_amount", "currency"]
    df = pd.DataFrame(
        [
            {
                "asin": "A1",
                "return_date": datetime(2024, 1, 1),
                "qty": 1,
                "refund_amount": 5.0,
                "currency": "USD",
            },
            {
                "asin": "A2",
                "return_date": datetime(2024, 1, 2),
                "qty": 2,
                "refund_amount": 10.0,
                "currency": "USD",
            },
        ]
    )
    copy_df_via_temp(
        engine,
        df,
        target_table="returns_raw",
        target_schema="test_ingest",
        columns=cols,
    )
    copy_df_via_temp(
        engine,
        df,
        target_table="returns_raw",
        target_schema="test_ingest",
        columns=cols,
    )
    with engine.connect() as conn:
        cnt = conn.execute(
            text("SELECT count(*) FROM test_ingest.returns_raw")
        ).scalar()
    assert cnt == 4


def test_null_handling(engine):
    cols = ["reimb_id", "reimb_date", "qty", "amount", "currency", "asin"]
    df = pd.DataFrame(
        [
            {
                "reimb_id": "rnull",
                "reimb_date": datetime(2024, 1, 3),
                "qty": 1,
                "amount": np.nan,
                "currency": "",
                "asin": "A",
            }
        ]
    )
    copy_df_via_temp(
        engine,
        df,
        target_table="reimbursements_raw",
        target_schema="test_ingest",
        columns=cols,
        conflict_cols=("reimb_id",),
    )
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT amount, currency FROM test_ingest.reimbursements_raw WHERE reimb_id='rnull'"
            )
        ).one()
    assert row.amount is None
    assert row.currency is None
