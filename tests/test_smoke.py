import importlib

import pytest
from fastapi.testclient import TestClient

from services.api import main as api_main

# Import service modules to exercise import paths
importlib.import_module("services.api.main")
importlib.import_module("services.repricer.app.main")
importlib.import_module("services.llm_server.app")


async def _noop() -> None:
    return None


@pytest.mark.parametrize("_", range(5))
def test_health_smoke(monkeypatch, _):
    monkeypatch.setattr(api_main, "_wait_for_db", _noop, raising=False)
    monkeypatch.setattr(api_main, "_check_llm", _noop, raising=False)
    with TestClient(api_main.app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
