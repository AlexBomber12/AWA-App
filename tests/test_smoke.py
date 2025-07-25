import importlib

import pytest
from fastapi.testclient import TestClient

from services.api import main


async def _dummy_get_session():
    class Dummy:
        async def execute(self, *_args, **_kwargs):
            return None

    yield Dummy()


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


async def _noop():
    return None


def test_health(monkeypatch) -> None:
    monkeypatch.setattr(main, "_wait_for_db", _noop)
    main.app.dependency_overrides[main.get_session] = _dummy_get_session
    with TestClient(main.app) as client:
        for _ in range(5):
            assert client.get("/health").json() == {"status": "ok"}
    main.app.dependency_overrides.clear()
