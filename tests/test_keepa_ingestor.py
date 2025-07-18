"""Tests for keepa_ingestor offline mode."""
# ruff: noqa: E402

import os
import shutil
import sys
import types
from pathlib import Path

# Stub external modules
sys.modules["keepa"] = types.SimpleNamespace(Keepa=lambda key: None)
sys.modules["minio"] = types.SimpleNamespace(Minio=lambda *a, **k: None)

from services.etl import keepa_ingestor


def test_keepa_ingestor_offline(tmp_path, monkeypatch):
    fixtures = Path(__file__).parent / "fixtures"
    dest = tmp_path / "tests/fixtures"
    dest.mkdir(parents=True)
    shutil.copy(fixtures / "keepa_sample.json", dest / "keepa_sample.json")
    monkeypatch.chdir(tmp_path)
    os.environ.pop("ENABLE_LIVE", None)
    keepa_ingestor.main()
    assert Path("tmp/offline_asins.json").exists()
