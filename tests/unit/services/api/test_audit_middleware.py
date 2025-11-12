from __future__ import annotations

from typing import Any

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from awa_common.security.models import Role, UserCtx
from services.api import security
from services.api.middlewares.audit import AuditMiddleware


@pytest.fixture
def audit_app(monkeypatch: pytest.MonkeyPatch):  # noqa: C901
    sink: list[dict[str, Any]] = []
    state: dict[str, Any] = {"fail_once": False}

    async def _fake_insert(_session, record: dict[str, Any]) -> None:  # type: ignore[override]
        if state["fail_once"]:
            state["fail_once"] = False
            raise RuntimeError("audit insert failed")
        sink.append(dict(record))

    class DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def commit(self):
            return None

    def session_factory() -> DummySession:
        return DummySession()

    async def _stub_validate(token: str, *, cfg=None) -> UserCtx:
        mapping = {
            "viewer": [Role.viewer],
            "ops": [Role.ops],
            "admin": [Role.admin],
        }
        roles = mapping.get(token)
        if roles is None:
            raise security.oidc.OIDCValidationError("invalid token")
        return UserCtx(
            sub=f"sub:{token}",
            email=f"{token}@example.com",
            roles=roles,
            raw_claims={"token": token},
        )

    monkeypatch.setattr("services.api.middlewares.audit.insert_audit", _fake_insert, raising=True)
    monkeypatch.setattr(security.oidc, "validate_access_token", _stub_validate, raising=True)
    monkeypatch.setattr(security.settings, "SECURITY_ENABLE_AUDIT", True, raising=False)

    app = FastAPI()
    app.add_middleware(security.RequestContextMiddleware)
    app.add_middleware(AuditMiddleware, session_factory=session_factory)

    @app.get("/viewer")
    async def viewer_route(
        request: Request,
        user: UserCtx = Depends(security.require_roles(Role.viewer, Role.ops, Role.admin)),
    ) -> dict[str, Any]:
        return {"status": "ok", "sub": user.sub}

    @app.get("/health")
    async def health_route(
        request: Request,
        user: UserCtx = Depends(security.require_roles(Role.viewer, Role.ops, Role.admin)),
    ) -> dict[str, Any]:
        return {"status": "ok", "sub": user.sub}

    @app.get("/ready")
    async def ready_route(
        request: Request,
        user: UserCtx = Depends(security.require_roles(Role.viewer, Role.ops, Role.admin)),
    ) -> dict[str, Any]:
        return {"status": "ok", "sub": user.sub}

    @app.get("/metrics")
    async def metrics_route(
        request: Request,
        user: UserCtx = Depends(security.require_roles(Role.viewer, Role.ops, Role.admin)),
    ) -> dict[str, Any]:
        return {"status": "ok", "sub": user.sub}

    return TestClient(app), sink, state


def test_audit_middleware_records_and_skips_paths(audit_app):
    client, sink, state = audit_app

    headers = {"Authorization": "Bearer viewer", "X-Request-ID": "req-123"}
    response = client.get("/viewer", headers=headers)
    assert response.status_code == 200
    assert len(sink) == 1

    record = sink[0]
    assert record["user_id"] == "sub:viewer"
    assert record["email"] == "viewer@example.com"
    assert record["roles"] == "{viewer}"
    assert record["path"] == "/viewer"
    assert record["method"] == "GET"
    assert record["status"] == 200
    assert record["request_id"] == "req-123"

    for path in ("/health", "/ready", "/metrics"):
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200
    assert len(sink) == 1

    state["fail_once"] = True
    resp_fail = client.get("/viewer", headers=headers)
    assert resp_fail.status_code == 200
    assert len(sink) == 1

    resp_recover = client.get("/viewer", headers=headers)
    assert resp_recover.status_code == 200
    assert len(sink) == 2
