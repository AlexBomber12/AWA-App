from sqlalchemy import create_engine, text
from services.common.db_url import build_url


def _setup_db():
    engine = create_engine(build_url(async_=False))
    with engine.begin() as conn:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(products)"))]
        if "status" not in cols:
            conn.execute(text("ALTER TABLE products ADD COLUMN status TEXT"))
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
        conn.execute(
            text(
                "INSERT OR IGNORE INTO vendor_prices(vendor_id, sku, cost) VALUES (1,'A1',10)"
            )
        )
        conn.execute(
            text(
                "INSERT OR IGNORE INTO vendor_prices(vendor_id, sku, cost) VALUES (1,'A2',25)"
            )
        )
        conn.execute(
            text(
                "INSERT OR IGNORE INTO keepa_offers(asin, buybox_price) VALUES ('A1',30)"
            )
        )
        conn.execute(
            text(
                "INSERT OR IGNORE INTO keepa_offers(asin, buybox_price) VALUES ('A2',30)"
            )
        )
        conn.execute(
            text(
                "INSERT OR IGNORE INTO fees_raw(asin, fulfil_fee, referral_fee, storage_fee, currency) VALUES ('A1',1,1,1,'EUR')"
            )
        )
        conn.execute(
            text(
                "INSERT OR IGNORE INTO fees_raw(asin, fulfil_fee, referral_fee, storage_fee, currency) VALUES ('A2',1,1,1,'EUR')"
            )
        )
        conn.execute(
            text(
                "INSERT OR IGNORE INTO freight_rates(lane, mode, eur_per_kg) VALUES ('EU→IT','sea',1)"
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
