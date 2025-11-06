import inspect
import uuid
from typing import Any

import pytest
from awa_common.security.models import Role, UserCtx
from awa_common.settings import parse_rate_limit
from fastapi import Depends, FastAPI, Request, Response
from fastapi.testclient import TestClient
from fastapi_limiter.depends import RateLimiter

from services.api import security


@pytest.fixture
def security_app(monkeypatch: pytest.MonkeyPatch):
    limiter_calls: list[dict[str, Any]] = []

    original_signature = inspect.signature(RateLimiter.__call__)  # type: ignore[arg-type]

    async def _record_rate_call(self, request: Request, response: Response) -> None:  # type: ignore[override]
        limiter_calls.append(
            {
                "path": request.url.path,
                "times": self.times,
                "window_seconds": int(self.milliseconds / 1000),
            }
        )

    _record_rate_call.__annotations__ = {
        "request": Request,
        "response": Response,
        "return": type(None),
    }
    _record_rate_call.__signature__ = original_signature  # type: ignore[attr-defined]

    monkeypatch.setattr(RateLimiter, "__call__", _record_rate_call, raising=False)

    def _stub_validate(token: str, *, cfg=None) -> UserCtx:
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
            raw_claims={"token": token, "roles": [role.value for role in roles]},
        )

    monkeypatch.setattr(security.oidc, "validate_access_token", _stub_validate, raising=True)

    app = FastAPI()
    app.add_middleware(security.RequestContextMiddleware)

    @app.get("/viewer")
    async def viewer_endpoint(
        request: Request,
        user: UserCtx = Depends(security.require_roles(Role.viewer, Role.ops, Role.admin)),
        _limit: None = Depends(security.limit_viewer()),
    ) -> dict[str, Any]:
        return {
            "sub": user.sub,
            "roles": [role.value for role in user.roles],
            "request_id": request.state.request_id,
        }

    @app.get("/ops")
    async def ops_endpoint(
        request: Request,
        user: UserCtx = Depends(security.require_roles(Role.ops, Role.admin)),
        _limit: None = Depends(security.limit_ops()),
    ) -> dict[str, Any]:
        return {
            "sub": user.sub,
            "roles": [role.value for role in user.roles],
            "request_id": request.state.request_id,
        }

    @app.get("/admin")
    async def admin_endpoint(
        request: Request,
        user: UserCtx = Depends(security.require_roles(Role.admin)),
        _limit: None = Depends(security.limit_admin()),
    ) -> dict[str, Any]:
        return {
            "sub": user.sub,
            "roles": [role.value for role in user.roles],
            "request_id": request.state.request_id,
        }

    client = TestClient(app)
    try:
        yield client, limiter_calls
    finally:
        client.close()


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_security_routes_behaviour(security_app):
    client, limiter_calls = security_app

    resp = client.get("/viewer")
    assert resp.status_code == 401
    assert resp.headers.get("WWW-Authenticate") == "Bearer"

    resp_wrong_scheme = client.get("/viewer", headers={"Authorization": "Token viewer"})
    assert resp_wrong_scheme.status_code == 401

    resp_viewer = client.get(
        "/viewer",
        headers={
            **_auth_header("viewer"),
            "X-Request-ID": "abc-request",
        },
    )
    assert resp_viewer.status_code == 200, resp_viewer.text
    body = resp_viewer.json()
    assert body["sub"] == "sub:viewer"
    assert body["roles"] == ["viewer"]
    assert body["request_id"] == "abc-request"

    resp_viewer_ops = client.get("/ops", headers=_auth_header("viewer"))
    assert resp_viewer_ops.status_code == 403

    resp_viewer_admin = client.get("/admin", headers=_auth_header("viewer"))
    assert resp_viewer_admin.status_code == 403

    resp_ops = client.get("/ops", headers=_auth_header("ops"))
    assert resp_ops.status_code == 200
    assert resp_ops.json()["roles"] == ["ops"]

    resp_ops_admin = client.get("/admin", headers=_auth_header("ops"))
    assert resp_ops_admin.status_code == 403

    resp_admin = client.get("/admin", headers=_auth_header("admin"))
    assert resp_admin.status_code == 200
    assert resp_admin.json()["roles"] == ["admin"]

    resp_request_id_generated = client.get("/viewer", headers=_auth_header("viewer"))
    assert resp_request_id_generated.status_code == 200
    generated_id = resp_request_id_generated.json()["request_id"]
    uuid.UUID(generated_id)

    expected_limits = {
        "/viewer": parse_rate_limit(security.settings.RATE_LIMIT_VIEWER),
        "/ops": parse_rate_limit(security.settings.RATE_LIMIT_OPS),
        "/admin": parse_rate_limit(security.settings.RATE_LIMIT_ADMIN),
    }

    for path, (times, seconds) in expected_limits.items():
        path_calls = [entry for entry in limiter_calls if entry["path"] == path]
        assert path_calls, f"rate limiter not invoked for {path}"
        latest = path_calls[-1]
        assert latest["times"] == times
        assert latest["window_seconds"] == seconds
