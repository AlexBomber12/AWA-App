import sqlite3
from pathlib import Path
import os
from importlib import import_module

importer = import_module("services.price_importer.import")


def test_roi_view(monkeypatch):
    monkeypatch.setenv("ENABLE_LIVE", "0")
    data_dir = Path(os.environ["DATA_DIR"])
    sample = Path("tests/fixtures/sample_prices.csv")
    importer.main([str(sample), "--vendor", "ACME GmbH"])
    db = sqlite3.connect(data_dir / "awa.db")
    db.execute("DROP TABLE IF EXISTS fees_raw")
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS fees_raw (
            asin TEXT PRIMARY KEY,
            fulfil_fee NUMERIC(10,2) NOT NULL,
            referral_fee NUMERIC(10,2) NOT NULL,
            storage_fee NUMERIC(10,2) NOT NULL DEFAULT 0,
            currency CHAR(3) NOT NULL DEFAULT '€',
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            asin TEXT PRIMARY KEY,
            title TEXT,
            brand TEXT,
            category TEXT,
            weight_kg NUMERIC
        );
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS keepa_offers (
            asin TEXT PRIMARY KEY,
            buybox_price NUMERIC(10,2)
        );
        """
    )
    db.execute(
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
    db.execute(
        """
        CREATE VIEW IF NOT EXISTS v_roi_full AS
        SELECT
          p.asin,
          (
            SELECT cost FROM vendor_prices vp
            WHERE vp.sku = p.asin
            ORDER BY vp.updated_at DESC
            LIMIT 1
          ) AS cost,
          f.fulfil_fee,
          f.referral_fee,
          f.storage_fee,
          k.buybox_price,
          (
            COALESCE(p.weight_kg, 0) *
            COALESCE((SELECT eur_per_kg FROM freight_rates LIMIT 1), 0)
          ) AS freight_cost,
          ROUND(
            100 * (
              k.buybox_price
              - (
                    SELECT cost FROM vendor_prices vp
                    WHERE vp.sku = p.asin
                    ORDER BY vp.updated_at DESC
                    LIMIT 1
                )
              - f.fulfil_fee
              - f.referral_fee
              - f.storage_fee
              - (
                    COALESCE(p.weight_kg, 0) *
                    COALESCE((SELECT eur_per_kg FROM freight_rates LIMIT 1), 0)
                )
            ) / k.buybox_price,
          2) AS roi_pct
        FROM products p
        JOIN keepa_offers k ON k.asin = p.asin
        JOIN fees_raw f ON f.asin = p.asin;
        """
    )
    db.execute("INSERT OR IGNORE INTO products(asin) VALUES ('A1')")
    db.execute("INSERT INTO keepa_offers(asin, buybox_price) VALUES ('A1', 25)")
    db.execute(
        "INSERT INTO fees_raw(asin, fulfil_fee, referral_fee, storage_fee, currency, updated_at) VALUES ('A1',1,1,1,'EUR','2024-01-01')"
    )
    db.execute(
        "INSERT OR IGNORE INTO freight_rates(lane, mode, eur_per_kg) VALUES ('EU→IT','sea',1)"
    )
    roi = db.execute("SELECT roi_pct FROM v_roi_full WHERE asin='A1'").fetchone()[0]
    assert roi is not None
    db.close()
