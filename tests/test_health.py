import pytest
from fastapi.testclient import TestClient

from services.api import main


async def _dummy_get_session():
    class Dummy:
        async def execute(self, *_args, **_kwargs):
            return None

    yield Dummy()


async def _noop() -> None:  # pragma: no cover - used only for monkeypatch
    return None


@pytest.mark.parametrize("_", range(5))
def test_health(monkeypatch, _):
    monkeypatch.setattr(main, "_wait_for_db", _noop)
    monkeypatch.setattr(main, "_check_llm", _noop)
    main.app.dependency_overrides[main.get_session] = _dummy_get_session
    with TestClient(main.app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
    main.app.dependency_overrides.clear()
