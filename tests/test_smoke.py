import importlib

import pytest
from fastapi.testclient import TestClient

from services.api import db, main


@pytest.mark.parametrize(
    "pkg",
    [
        "services.api",
        "services.fees_h10",
        "services.logistics_etl",
        "services.worker.repricer.app.main",
        "services.worker",
        "services.emailer",
        "services.alert_bot",
        "services.price_importer",
    ],
)
def test_import(pkg) -> None:
    importlib.import_module(pkg)


class FakeSession:
    async def execute(self, query):
        class R:
            def scalar(self):
                import datetime

                return datetime.datetime.utcnow()

        return R()


async def fake_get_session():
    yield FakeSession()


async def _noop() -> None:
    return None


@pytest.mark.parametrize("_", range(5))
def test_health(monkeypatch, _) -> None:
    monkeypatch.setattr(main, "_wait_for_db", _noop)
    monkeypatch.setattr(main, "_check_llm", _noop)
    app = main.app
    app.dependency_overrides[db.get_session] = fake_get_session
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
    app.dependency_overrides.clear()
