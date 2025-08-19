import os, threading
from sqlalchemy import text
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.slow]

def test_concurrent_upserts_no_deadlock(pg_engine, ensure_test_logistics_table):
    os.environ["TESTING"] = "1"
    from services.logistics_etl import repository as repo

    def worker(price, barrier, done):
        barrier.wait()
        repo._upsert_many_with_keys(
            pg_engine,
            table="test_logistics_routes",
            key_cols=["lane_id"],
            rows=[{"lane_id": "LZ", "carrier": "C1", "eur_per_kg": price}],
            update_columns=["eur_per_kg", "updated_at"],
            testing=False,
        )
        done.append(price)

    barrier = threading.Barrier(2)
    done1, done2 = [], []
    t1 = threading.Thread(target=worker, args=(5.00, barrier, done1))
    t2 = threading.Thread(target=worker, args=(5.20, barrier, done2))
    t1.start(); t2.start(); t1.join(timeout=10); t2.join(timeout=10)
    assert not t1.is_alive() and not t2.is_alive(), "Deadlock or hang in concurrent upserts"

    with pg_engine.connect() as c:
        val = float(
            c.execute(
                text("SELECT eur_per_kg FROM test_logistics_routes WHERE lane_id='LZ'")
            ).scalar_one()
        )
    assert val in (5.00, 5.20)
