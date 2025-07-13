import importlib
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from services.logistics_etl import repository


@pytest.mark.asyncio
async def test_upsert_many(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ENABLE_LIVE", "0")
    importlib.reload(repository)
    db_path = Path(tmp_path) / "awa.db"
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE freight_rates (
                lane TEXT,
                mode TEXT,
                eur_per_kg NUMERIC(10,2),
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (lane, mode)
            );
            """
        )
    rows = [
        {"lane": "CN->DE", "mode": "sea", "eur_per_kg": 1.0},
        {"lane": "CN->DE", "mode": "air", "eur_per_kg": 5.0},
    ]
    await repository.upsert_many(rows)
    await repository.upsert_many([{"lane": "CN->DE", "mode": "sea", "eur_per_kg": 2.0}])
    with engine.connect() as conn:
        cnt = conn.execute(text("SELECT count(*) FROM freight_rates")).scalar()
        val = conn.execute(
            text("SELECT eur_per_kg FROM freight_rates WHERE lane='CN->DE' AND mode='sea'")
        ).scalar()
    assert cnt == 2
    assert float(val) == 2.0
