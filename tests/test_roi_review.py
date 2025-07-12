from sqlalchemy import create_engine, text
from services.common.db_url import build_url


def _setup_db():
    engine = create_engine(build_url(async_=False))
    with engine.begin() as conn:
        if engine.dialect.name == "sqlite":
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
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(products)"))]
            if "status" not in cols:
                conn.execute(text("ALTER TABLE products ADD COLUMN status TEXT"))
            insert_vendor = "INSERT OR IGNORE INTO vendor_prices(vendor_id, sku, cost) VALUES (:vid,:sku,:cost)"
            insert_keepa = "INSERT OR IGNORE INTO keepa_offers(asin, buybox_price) VALUES (:asin,:price)"
            insert_fee = "INSERT OR IGNORE INTO fees_raw(asin, fulfil_fee, referral_fee, storage_fee, currency) VALUES (:asin,1,1,1,'EUR')"
        else:
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
            try:
                conn.execute(text("ALTER TABLE products ADD COLUMN status TEXT"))
            except Exception:
                pass
            conn.execute(
                text(
                    "INSERT INTO vendors(id, name) VALUES (1,'ACME GmbH') ON CONFLICT DO NOTHING"
                )
            )
            insert_vendor = "INSERT INTO vendor_prices(vendor_id, sku, cost) VALUES (:vid,:sku,:cost) ON CONFLICT DO NOTHING"
            insert_keepa = "INSERT INTO keepa_offers(asin, buybox_price) VALUES (:asin,:price) ON CONFLICT DO NOTHING"
            insert_fee = "INSERT INTO fees_raw(asin, fulfil_fee, referral_fee, storage_fee, currency) VALUES (:asin,1,1,1,'EUR') ON CONFLICT DO NOTHING"
        if engine.dialect.name == "sqlite":
            conn.execute(
                text("INSERT OR IGNORE INTO vendors(id, name) VALUES (1,'ACME GmbH')")
            )
            conn.execute(
                text(
                    "INSERT OR IGNORE INTO products(asin, title, category, weight_kg) VALUES ('A1','t1','cat',1)"
                )
            )
            conn.execute(
                text(
                    "INSERT OR IGNORE INTO products(asin, title, category, weight_kg) VALUES ('A2','t2','cat',1)"
                )
            )
        else:
            conn.execute(
                text(
                    "INSERT INTO products(asin, title, category, weight_kg) VALUES ('A1','t1','cat',1) ON CONFLICT DO NOTHING"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO products(asin, title, category, weight_kg) VALUES ('A2','t2','cat',1) ON CONFLICT DO NOTHING"
                )
            )
        conn.execute(text(insert_vendor), {"vid": 1, "sku": "A1", "cost": 10})
        conn.execute(text(insert_vendor), {"vid": 1, "sku": "A2", "cost": 25})
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
        if engine.dialect.name == "sqlite":
            conn.execute(
                text(
                    "INSERT OR IGNORE INTO freight_rates(lane, mode, eur_per_kg) VALUES ('EU→IT','sea',1)"
                )
            )
        else:
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
    r = api_client.post(
        "/roi-review/approve", data={"asins": ["A1", "B1"]}, auth=("admin", "pass")
    )
    assert r.status_code == 200
    assert r.json()["count"] >= 1
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT status FROM products WHERE asin IN ('A1','B1') ORDER BY asin")
        )
        statuses = [row[0] for row in rows.fetchall()]
    assert statuses == ["approved", "approved"]
