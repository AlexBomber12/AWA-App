import importlib

import pytest
from sqlalchemy import create_engine

from services.price_importer.repository import Repository

importer = importlib.import_module("services.price_importer.import")

pytestmark = pytest.mark.integration


def test_import_cli(tmp_path, monkeypatch):
    csv = tmp_path / "price.csv"
    csv.write_text("sku,cost\nA1,1.0\n")

    engine = create_engine(f"sqlite:///{tmp_path / 'db.sqlite'}", future=True)
    monkeypatch.setattr(
        Repository,
        "__init__",
        lambda self, engine=engine: setattr(self, "engine", engine),
    )
    monkeypatch.setattr(Repository, "ensure_vendor", lambda self, name: 1)
    monkeypatch.setattr(
        Repository, "upsert_prices", lambda self, vid, rows, dry_run: (len(rows), 0)
    )

    assert importer.main([str(csv), "--vendor", "ACME", "--dry-run"]) == 0
