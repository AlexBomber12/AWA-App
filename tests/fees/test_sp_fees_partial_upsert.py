import os

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integration


def _rows_phase1():
    return [
        {
            "asin": "B1",
            "marketplace": "US",
            "fee_type": "fba_pick_pack",
            "amount": 1.00,
            "currency": "USD",
            "source": "sp",
            "effective_date": "2024-02-01",
        },
        {
            "asin": "B2",
            "marketplace": "US",
            "fee_type": "fba_pick_pack",
            "amount": 2.00,
            "currency": "USD",
            "source": "sp",
            "effective_date": "2024-02-01",
        },
    ]


def _rows_phase2():  # B2 changes, B3 new
    return [
        {
            "asin": "B2",
            "marketplace": "US",
            "fee_type": "fba_pick_pack",
            "amount": 2.50,
            "currency": "USD",
            "source": "sp",
            "effective_date": "2024-02-01",
        },
        {
            "asin": "B3",
            "marketplace": "US",
            "fee_type": "fba_pick_pack",
            "amount": 3.00,
            "currency": "USD",
            "source": "sp",
            "effective_date": "2024-02-01",
        },
    ]


def _env():
    os.environ["TESTING"] = "1"
    os.environ["FEES_RAW_TABLE"] = "test_fees_raw"


def test_sp_fees_upsert_only_changes(pg_engine, ensure_test_fees_raw_table):
    _env()
    try:
        from services.fees_h10 import repository as repo
    except Exception:
        pytest.skip("repository helper not available")
    s1 = repo.upsert_fees_raw(pg_engine, _rows_phase1(), testing=True)
    assert s1 == {"inserted": 2, "updated": 0, "skipped": 0}
    s2 = repo.upsert_fees_raw(pg_engine, _rows_phase2(), testing=True)
    assert s2["inserted"] == 1 and s2["updated"] == 1 and s2["skipped"] == 0
    with pg_engine.connect() as c:
        amt = c.execute(
            text("SELECT amount FROM test_fees_raw WHERE asin='B2' AND fee_type='fba_pick_pack'")
        ).scalar_one()
    assert float(amt) == 2.50
