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
    db.execute("INSERT INTO products(asin) VALUES ('A1')")
    db.execute("INSERT INTO keepa_offers(asin, buybox_price) VALUES ('A1', 25)")
    db.execute(
        "INSERT INTO fees_raw(asin, fulf_fee, referral_fee, storage_fee, captured_at) VALUES ('A1',1,1,1,'2024-01-01')"
    )
    roi = db.execute("SELECT roi_pct FROM v_roi_full WHERE asin='A1'").fetchone()[0]
    assert roi is not None
