import types
import sys
from etl import run_etl


def test_run_etl(monkeypatch, tmp_path):
    calls = {"n": 0}

    class FakeKeepa:
        def __init__(self, key):
            pass

        def product_finder(self, query):
            calls["n"] += 1
            return ["x"]

    keepa_module = types.SimpleNamespace(Keepa=FakeKeepa)
    monkeypatch.setitem(sys.modules, "keepa", keepa_module)

    class FakeMinio:
        def __init__(self):
            self.path = None

        def fput_object(self, bucket, name, path):
            self.path = path

    class FakeLog:
        def __init__(self):
            self.called = False

        def insert(self, data):
            self.called = True

    minio_client = FakeMinio()
    log = FakeLog()
    file_path = run_etl("key", minio_client, log, tmp_path)
    assert calls["n"] == 1
    assert (tmp_path / file_path.name).exists()
    assert log.called
