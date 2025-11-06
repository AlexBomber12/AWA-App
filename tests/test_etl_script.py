import os
import shutil
import sys
import types
from pathlib import Path


def test_keepa_ingestor_main(tmp_path, monkeypatch, patch_etl_session):
    fixtures = Path(__file__).parent / "fixtures"
    dest = tmp_path / "tests/fixtures"
    dest.mkdir(parents=True)
    shutil.copy(fixtures / "keepa_sample.json", dest / "keepa_sample.json")
    monkeypatch.chdir(tmp_path)
    os.environ.pop("ENABLE_LIVE", None)
    sys.modules["keepa"] = types.SimpleNamespace(Keepa=lambda k: None)
    sys.modules["minio"] = types.SimpleNamespace(Minio=lambda *a, **k: None)
    patch_etl_session("services.etl.keepa_ingestor")
    from services.etl import keepa_ingestor

    assert keepa_ingestor.main([]) == 0
    assert (tmp_path / "tmp/offline_asins.json").exists()
