import importlib
import shutil

import pytest
from alembic import command  # type: ignore[attr-defined]
from alembic.config import Config
from httpx import Response
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine

pytestmark = pytest.mark.integration

pytest.importorskip("apscheduler")
respx = pytest.importorskip("respx")

from awa_common import db_url, dsn  # noqa: E402
from awa_common.settings import settings  # noqa: E402

from services.logistics_etl import client, cron, repository  # noqa: E402


@respx.mock
@pytest.mark.skipif(shutil.which("pg_ctl") is None, reason="pg_ctl not installed")
@pytest.mark.asyncio
async def test_job_inserts_and_affects_roi(postgresql_proc, tmp_path, monkeypatch):
    dsn_async = (
        f"postgresql+asyncpg://{postgresql_proc.user}:{postgresql_proc.password or ''}"
        f"@{postgresql_proc.host}:{postgresql_proc.port}/{postgresql_proc.dbname}"
    )
    dsn_sync = (
        f"postgresql+psycopg://{postgresql_proc.user}:{postgresql_proc.password or ''}"
        f"@{postgresql_proc.host}:{postgresql_proc.port}/{postgresql_proc.dbname}"
    )
    monkeypatch.setattr(db_url, "build_url", lambda async_=False: dsn_async if async_ else dsn_sync)
    monkeypatch.setattr(dsn, "build_dsn", lambda sync=True: dsn_sync if sync else dsn_async)
    monkeypatch.setenv("DATABASE_URL", dsn_sync)
    settings.DATABASE_URL = dsn_sync  # type: ignore[attr-defined]
    importlib.reload(repository)
    repository._engine = create_async_engine(dsn_async, future=True)

    cfg = Config("services/api/alembic.ini")
    command.upgrade(cfg, "head")

    engine = create_engine(dsn_sync)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO products(asin, weight_kg) VALUES ('A1',1)"))
        conn.execute(text("INSERT INTO vendors(id, name) VALUES (1,'test')"))
        conn.execute(
            text(
                "INSERT INTO vendor_prices(vendor_id, sku, cost, updated_at) VALUES (1,'A1',2,'2024-01-01')"
            )
        )
        conn.execute(text("INSERT INTO keepa_offers(asin, buybox_price) VALUES ('A1',10)"))
        conn.execute(
            text(
                "INSERT INTO fees_raw(asin, fulfil_fee, referral_fee, storage_fee, currency, updated_at) VALUES ('A1',1,1,1,'EUR','2024-01-01')"
            )
        )

    csv_data = "lane,mode,eur_per_kg\nCN->DE,sea,2\n"
    respx.get(client.URL).mock(return_value=Response(200, text=csv_data))

    await cron.job()

    with engine.connect() as conn:
        cnt = conn.execute(text("SELECT count(*) FROM freight_rates")).scalar()
        roi = conn.execute(text("SELECT roi_pct FROM v_roi_full WHERE asin='A1'")).scalar()
    assert cnt == 1
    assert roi == 30.0
