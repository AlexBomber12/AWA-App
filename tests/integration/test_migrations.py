import pytest
from alembic import command  # type: ignore[attr-defined]
from alembic.config import Config  # type: ignore[attr-defined]
from awa_common.dsn import build_dsn
from sqlalchemy import create_engine, text

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


def test_run_migrations(tmp_path, monkeypatch, pg_pool):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ENABLE_LIVE", "0")
    db_path = tmp_path / "awa.db"
    if db_path.exists():
        db_path.unlink()
    cfg = Config("services/api/alembic.ini")
    command.upgrade(cfg, "head")
    command.upgrade(cfg, "head")
    engine = create_engine(build_dsn(sync=True))
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO products(asin) VALUES ('A1')"))
        conn.execute(
            text(
                "INSERT INTO offers(asin, seller_sku, price_cents, captured_at) VALUES ('A1','S1',1000,'2024-01-01')"
            )
        )
        conn.execute(text("INSERT INTO vendors(id, name) VALUES (1, 'test')"))
        conn.execute(
            text(
                "INSERT INTO vendor_prices(vendor_id, sku, cost, updated_at) VALUES (1,'A1',5,'2024-01-01')"
            )
        )
        conn.execute(text("INSERT INTO keepa_offers(asin, buybox_price) VALUES ('A1', 25)"))
        conn.execute(
            text(
                "INSERT INTO fees_raw(asin, fulfil_fee, referral_fee, storage_fee, currency, captured_at, updated_at) VALUES ('A1',1,1,1,'EUR','2024-01-01','2024-01-01')"
            )
        )
        count = conn.execute(text("SELECT COUNT(*) FROM roi_view")).scalar()
        assert count >= 0
