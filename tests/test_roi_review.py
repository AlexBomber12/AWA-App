import pytest
from awa_common.dsn import build_dsn
from sqlalchemy import create_engine, text

pytestmark = pytest.mark.integration


def _setup_db():
    engine = create_engine(build_dsn(sync=True))
    with engine.begin() as conn:
        # Ensure clean state for deterministic tests
        for tbl in [
            "vendor_prices",
            "keepa_offers",
            "fees_raw",
            "freight_rates",
            "offers",
            "products",
        ]:
            conn.execute(text(f"DELETE FROM {tbl}"))
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS products (
                    asin TEXT PRIMARY KEY,
                    title TEXT,
                    category TEXT,
                    weight_kg NUMERIC
                );
                """
            )
        )
        conn.execute(
            text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='products' AND column_name='status'
                    ) THEN
                        ALTER TABLE products ADD COLUMN status TEXT;
                    END IF;
                END
                $$;
                """
            )
        )
        conn.execute(
            text("INSERT INTO vendors(id, name) VALUES (1,'ACME GmbH') ON CONFLICT DO NOTHING")
        )
        insert_keepa = "INSERT INTO keepa_offers(asin, buybox_price) VALUES (:asin,:price) ON CONFLICT (asin) DO UPDATE SET buybox_price=EXCLUDED.buybox_price"
        insert_fee = "INSERT INTO fees_raw(asin, fulfil_fee, referral_fee, storage_fee, currency) VALUES (:asin,1,1,1,'EUR') ON CONFLICT (asin) DO UPDATE SET updated_at=CURRENT_TIMESTAMP"
        conn.execute(
            text(
                "INSERT INTO vendors(id, name) VALUES (1,'ACME GmbH') ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name"
            )
        )
        conn.execute(
            text(
                "INSERT INTO products(asin, title, category, weight_kg) VALUES ('A1','t1','cat',1) ON CONFLICT (asin) DO UPDATE SET title=EXCLUDED.title"
            )
        )
        conn.execute(
            text(
                "INSERT INTO products(asin, title, category, weight_kg) VALUES ('A2','t2','cat',1) ON CONFLICT (asin) DO UPDATE SET title=EXCLUDED.title"
            )
        )
        conn.execute(
            text(
                "INSERT INTO vendors(id, name) VALUES (1,'ACME GmbH') ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name"
            )
        )
        conn.execute(
            text(
                "INSERT INTO vendor_prices(vendor_id, sku, cost) VALUES (1,'A1',10) ON CONFLICT (vendor_id, sku) DO UPDATE SET cost=EXCLUDED.cost"
            )
        )
        conn.execute(
            text(
                "INSERT INTO vendor_prices(vendor_id, sku, cost) VALUES (1,'A2',25) ON CONFLICT (vendor_id, sku) DO UPDATE SET cost=EXCLUDED.cost"
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS freight_rates (
                    lane TEXT,
                    mode TEXT,
                    eur_per_kg NUMERIC(10,2),
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (lane, mode)
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS keepa_offers (
                    asin TEXT PRIMARY KEY,
                    buybox_price NUMERIC(10,2)
                );
                """
            )
        )
        conn.execute(text(insert_keepa), {"asin": "A1", "price": 30})
        conn.execute(text(insert_keepa), {"asin": "A2", "price": 30})
        conn.execute(text(insert_fee), {"asin": "A1"})
        conn.execute(text(insert_fee), {"asin": "A2"})
        conn.execute(
            text(
                "INSERT INTO freight_rates(lane, mode, eur_per_kg) VALUES ('EU→IT','sea',1) ON CONFLICT DO NOTHING"
            )
        )
    return engine


def test_auth_guard(api_client, monkeypatch):
    monkeypatch.setenv("BASIC_USER", "admin")
    monkeypatch.setenv("BASIC_PASS", "pass")
    r = api_client.get("/roi-review")
    assert r.status_code == 401


def test_filter_roi(api_client, monkeypatch):
    monkeypatch.setenv("BASIC_USER", "admin")
    monkeypatch.setenv("BASIC_PASS", "pass")
    _setup_db()
    r = api_client.get("/roi-review?roi_min=20", auth=("admin", "pass"))
    assert r.status_code == 200
    assert "A1" in r.text
    assert "A2" not in r.text


def test_bulk_approve(api_client, monkeypatch):
    monkeypatch.setenv("BASIC_USER", "admin")
    monkeypatch.setenv("BASIC_PASS", "pass")
    engine = _setup_db()
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO products(asin, status) VALUES ('B1','pending')"))
    r = api_client.post("/roi-review/approve", data={"asins": ["A1", "B1"]}, auth=("admin", "pass"))
    assert r.status_code == 200
    assert r.json()["updated"] >= 1
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT status FROM products WHERE asin IN ('A1','B1') ORDER BY asin")
        )
        statuses = [row[0] for row in rows.fetchall()]
    assert statuses == ["approved", "approved"]
