import pytest
from fastapi.testclient import TestClient

from services.api import db, main
from tests.helpers.api import prepare_api_for_tests

pytestmark = pytest.mark.slow


@pytest.mark.slow
@pytest.mark.timeout(0)
@pytest.mark.parametrize("_", range(5))
def test_health(monkeypatch, _):
    prepare_api_for_tests(monkeypatch)

    class FakeSession:
        async def execute(self, query):
            class R:
                def scalar(self):
                    from datetime import UTC, datetime

                    return datetime.now(UTC)

            return R()

    async def fake_get_session():
        yield FakeSession()

    main.app.dependency_overrides[db.get_session] = fake_get_session
    with TestClient(main.app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
    main.app.dependency_overrides.clear()
