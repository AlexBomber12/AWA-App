import pytest
from fastapi.testclient import TestClient

from services.api import db, main


async def _noop() -> None:  # pragma: no cover - used only for monkeypatch
    return None


@pytest.mark.parametrize("_", range(5))
def test_health(monkeypatch, _):
    monkeypatch.setattr(main, "_wait_for_db", _noop)
    monkeypatch.setattr(main, "_check_llm", _noop)

    class FakeSession:
        async def execute(self, query):
            class R:
                def scalar(self):
                    import datetime

                    return datetime.datetime.utcnow()

            return R()

    async def fake_get_session():
        yield FakeSession()

    main.app.dependency_overrides[db.get_session] = fake_get_session
    with TestClient(main.app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
    main.app.dependency_overrides.clear()
