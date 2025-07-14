import importlib

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

from services.logistics_etl import repository


@pytest.mark.asyncio
async def test_upsert_many(pg_engine):
    importlib.reload(repository)
    async_engine = create_async_engine(
        str(pg_engine.url).replace("postgresql://", "postgresql+asyncpg://"),
        future=True,
    )
    repository._engine = async_engine

    with pg_engine.begin() as conn:
        conn.exec_driver_sql("TRUNCATE freight_rates")

    data = [
        {"lane": "EU-IT\u2192US", "mode": "air", "eur_per_kg": 7.55},
        {"lane": "EU-IT\u2192US", "mode": "sea", "eur_per_kg": 2.10},
    ]
    await repository.upsert_many(data)

    with pg_engine.connect() as conn:
        rows = conn.execute(sa.text("SELECT COUNT(*) FROM freight_rates")).scalar()
    assert rows == 2
