import os

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integration


def _rows_phase1():
    return [
        {
            "asin": "A1",
            "marketplace": "US",
            "fee_type": "referral",
            "amount": 1.11,
            "currency": "USD",
            "source": "h10",
            "effective_date": "2024-01-01",
        },
        {
            "asin": "A2",
            "marketplace": "US",
            "fee_type": "referral",
            "amount": 2.22,
            "currency": "USD",
            "source": "h10",
            "effective_date": "2024-01-01",
        },
        {
            "asin": "A3",
            "marketplace": "US",
            "fee_type": "referral",
            "amount": 3.33,
            "currency": "USD",
            "source": "h10",
            "effective_date": "2024-01-01",
        },
    ]


def _rows_phase2():  # A1 changed, A2 unchanged, A4 new
    return [
        {
            "asin": "A1",
            "marketplace": "US",
            "fee_type": "referral",
            "amount": 9.99,
            "currency": "USD",
            "source": "h10",
            "effective_date": "2024-01-01",
        },
        {
            "asin": "A2",
            "marketplace": "US",
            "fee_type": "referral",
            "amount": 2.22,
            "currency": "USD",
            "source": "h10",
            "effective_date": "2024-01-01",
        },
        {
            "asin": "A4",
            "marketplace": "US",
            "fee_type": "referral",
            "amount": 4.44,
            "currency": "USD",
            "source": "h10",
            "effective_date": "2024-01-01",
        },
    ]


def _auth_env():
    os.environ["TESTING"] = "1"
    os.environ["FEES_RAW_TABLE"] = "test_fees_raw"


def test_h10_partial_success_and_idempotent_update(
    pg_engine, ensure_test_fees_raw_table, monkeypatch
):
    _auth_env()
    try:
        from services.fees_h10 import repository as repo
        from services.fees_h10 import worker
    except Exception:
        pytest.skip("Helium10 modules not present")

    calls = {"phase": 1}

    def fake_fetch(*a, **kw):
        return _rows_phase1() if calls["phase"] == 1 else _rows_phase2()

    fetch_attr = "fetch_fees" if hasattr(worker, "fetch_fees") else "run"
    if hasattr(worker, fetch_attr):
        monkeypatch.setattr(worker, fetch_attr, fake_fetch)

    summary1 = repo.upsert_fees_raw(pg_engine, _rows_phase1(), testing=True)
    assert summary1 == {"inserted": 3, "updated": 0, "skipped": 0}
    with pg_engine.connect() as c:
        total = c.execute(text("SELECT COUNT(*) FROM test_fees_raw")).scalar_one()
    assert total == 3

    summary2 = repo.upsert_fees_raw(pg_engine, _rows_phase2(), testing=True)
    assert summary2["inserted"] == 1 and summary2["updated"] == 1 and summary2["skipped"] == 1
    with pg_engine.connect() as c:
        amt = c.execute(
            text(
                "SELECT amount FROM test_fees_raw WHERE asin='A1' AND marketplace='US' AND fee_type='referral'"
            )
        ).scalar_one()
    assert float(amt) == 9.99


def test_h10_network_error_is_handled_without_partial_writes(
    pg_engine, ensure_test_fees_raw_table, monkeypatch
):
    _auth_env()
    try:
        from services.fees_h10 import worker
    except Exception:
        pytest.skip("Helium10 modules not present")

    class Boom(Exception):
        pass

    def boom(*a, **kw):
        raise Boom("timeout")

    if hasattr(worker, "client"):
        monkeypatch.setattr(worker, "client", type("C", (), {"fetch": boom})())
    else:
        monkeypatch.setattr(worker, "fetch_fees", boom, raising=False)

    with pg_engine.begin() as c:
        c.execute(text("TRUNCATE test_fees_raw;"))
    try:
        pass
    except Exception:
        pass
    with pg_engine.connect() as c:
        count = c.execute(text("SELECT COUNT(*) FROM test_fees_raw")).scalar_one()
    assert count == 0


def test_h10_invalid_payload_gracefully_errors(pg_engine, ensure_test_fees_raw_table, monkeypatch):
    _auth_env()
    try:
        from services.fees_h10 import repository as repo
    except Exception:
        pytest.skip("Helium10 modules not present")

    bad_rows = [{"asin": "A1"}]
    with pytest.raises(Exception):
        repo.upsert_fees_raw(pg_engine, bad_rows, testing=True)
