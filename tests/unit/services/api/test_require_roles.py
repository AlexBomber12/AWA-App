from __future__ import annotations

import pytest
from awa_common.security.models import Role, UserCtx
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from services.api import security


def _make_user(*roles: Role) -> UserCtx:
    return UserCtx(sub="user", email="user@example.com", roles=list(roles), raw_claims={})


def _build_app(required_roles: tuple[Role, ...]) -> TestClient:
    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(security.require_roles(*required_roles))])
    def protected(_: UserCtx = Depends(security.current_user)) -> dict[str, str]:
        return {"status": "ok"}

    return TestClient(app)


def test_route_allows_user_with_required_role(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(security, "current_user", lambda: _make_user(Role.viewer))
    client = _build_app((Role.viewer,))
    response = client.get("/protected")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_route_rejects_user_without_role(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(security, "current_user", lambda: _make_user(Role.viewer))
    client = _build_app((Role.admin,))
    response = client.get("/protected")
    assert response.status_code == 403
