import os

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integration


def test_updates_only_whitelisted_columns(pg_engine, ensure_test_logistics_table):
    os.environ["TESTING"] = "1"
    os.environ["LOGISTICS_TEST_TABLE"] = "test_logistics_routes"
    from services.logistics_etl import repository as repo

    rows1 = [
        {"lane_id": "L1", "carrier": "DHL", "eur_per_kg": 3.50},
        {"lane_id": "L2", "carrier": "UPS", "eur_per_kg": 4.10},
    ]
    # initial insert
    s1 = repo._upsert_many_with_keys(
        pg_engine,
        table="test_logistics_routes",
        key_cols=["lane_id"],
        rows=rows1,
        update_columns=["eur_per_kg", "updated_at"],
        testing=True,
    )
    assert s1 == {"inserted": 2, "updated": 0, "skipped": 0}

    # second batch: change carrier (should NOT update), change eur_per_kg (should update)
    rows2 = [
        {"lane_id": "L1", "carrier": "FedEx", "eur_per_kg": 3.90},
        {"lane_id": "L2", "carrier": "UPS", "eur_per_kg": 4.10},
    ]
    s2 = repo._upsert_many_with_keys(
        pg_engine,
        table="test_logistics_routes",
        key_cols=["lane_id"],
        rows=rows2,
        update_columns=["eur_per_kg", "updated_at"],
        testing=True,
    )
    assert s2["inserted"] == 0 and s2["updated"] == 1 and s2["skipped"] == 1

    with pg_engine.connect() as c:
        res = dict(
            c.execute(text("SELECT lane_id, carrier, eur_per_kg FROM test_logistics_routes WHERE lane_id='L1'"))
            .mappings()
            .first()
        )
        assert res["carrier"] == "DHL"
        assert float(res["eur_per_kg"]) == 3.90
