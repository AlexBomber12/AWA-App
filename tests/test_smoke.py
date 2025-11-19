import importlib

import pytest
from fastapi.testclient import TestClient

from services.api import db, main
from tests.helpers.api import prepare_api_for_tests

pytestmark = pytest.mark.slow


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
                from datetime import UTC, datetime

                return datetime.now(UTC)

        return R()


async def fake_get_session():
    yield FakeSession()


@pytest.mark.slow
@pytest.mark.timeout(0)
@pytest.mark.parametrize("_", range(5))
def test_health(monkeypatch, _) -> None:
    prepare_api_for_tests(monkeypatch)
    app = main.app
    app.dependency_overrides[db.get_session] = fake_get_session
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
    app.dependency_overrides.clear()
