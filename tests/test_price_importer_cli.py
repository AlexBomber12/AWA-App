from importlib import import_module
from pathlib import Path

from sqlalchemy import create_engine, text

from services.price_importer.repository import Repository

imp = import_module("services.price_importer.import")


def test_price_importer_cli(tmp_path, monkeypatch):
    csv = Path("tests/fixtures/sample_prices.csv")
    db = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db}")
    assert imp.main([str(csv), "--vendor", "acme"]) == 0

    repo = Repository(create_engine(f"sqlite:///{db}"))
    with repo.engine.connect() as conn:
        cnt = conn.execute(text("SELECT count(*) FROM vendor_prices")).scalar()
    assert cnt > 0
