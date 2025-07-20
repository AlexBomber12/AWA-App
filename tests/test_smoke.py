import importlib

import pytest
from fastapi.testclient import TestClient

from services.api.main import app


@pytest.mark.parametrize(
    "pkg",
    [
        "services.api",
        "services.fees_h10",
        "services.logistics_etl",
        "services.repricer.app.main",
        "services.ingest",
        "services.emailer",
        "services.alert_bot",
        "services.price_importer",
    ],
)
def test_import(pkg) -> None:
    importlib.import_module(pkg)


client = TestClient(app)


def test_health() -> None:
    for _ in range(5):
        assert client.get("/health").json() == {"status": "ok"}
