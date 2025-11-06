from __future__ import annotations

from collections import defaultdict
from typing import Any

from awa_common.security.models import Role, UserCtx
from awa_common.security.ratelimit import install_role_based_rate_limit
from awa_common.settings import parse_rate_limit, settings
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from fastapi_limiter import FastAPILimiter

from services.api import security


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_role_based_rate_limiter_enforces_by_role(monkeypatch):
    call_log: list[str] = []
    counters: dict[tuple[str, int], int] = defaultdict(int)

    class StubRateLimiter:
        def __init__(self, *, times: int, seconds: int, identifier=None, **_: Any) -> None:
            self.times = times
            self.seconds = seconds
            self.identifier = identifier

        async def __call__(self, request: Request, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
            call_log.append(request.url.path)
            if self.identifier:
                ident = self.identifier(request)
            else:  # pragma: no cover - defensive
                ident = "global"
            key = (ident, self.seconds)
            counters[key] += 1
            if counters[key] > self.times:
                raise HTTPException(status_code=429, detail="Too Many Requests")

    monkeypatch.setattr("awa_common.security.ratelimit.RateLimiter", StubRateLimiter, raising=True)
    monkeypatch.setattr(FastAPILimiter, "redis", object(), raising=False)
    monkeypatch.setattr(settings, "RATE_LIMIT_VIEWER", "2/minute", raising=False)
    monkeypatch.setattr(settings, "RATE_LIMIT_OPS", "4/minute", raising=False)
    monkeypatch.setattr(settings, "RATE_LIMIT_ADMIN", "6/minute", raising=False)

    def _build_user(token: str) -> UserCtx | None:
        mapping = {
            "viewer": [Role.viewer],
            "ops": [Role.ops],
            "admin": [Role.admin],
        }
        roles = mapping.get(token)
        if roles is None:
            return None
        return UserCtx(
            sub=token,
            email=f"{token}@example.com",
            roles=roles,
            raw_claims={"roles": [role.value for role in roles]},
        )

    async def attach_user(request: Request) -> None:
        auth = request.headers.get("Authorization", "")
        token = auth.split(" ", 1)[1].strip() if " " in auth else ""
        user = _build_user(token)
        if user is not None:
            request.state.user = user

    async def stub_current_user(request: Request) -> UserCtx:
        user = getattr(request.state, "user", None)
        if isinstance(user, UserCtx):
            return user
        auth = request.headers.get("Authorization", "")
        token = auth.split(" ", 1)[1].strip() if " " in auth else ""
        user = _build_user(token)
        if user is None:
            raise HTTPException(status_code=401, detail="Missing token")
        request.state.user = user
        return user

    app = FastAPI()
    app.router.dependencies.append(Depends(attach_user))
    install_role_based_rate_limit(app, settings)
    app.dependency_overrides[security.current_user] = stub_current_user

    @app.get("/viewer")
    async def viewer_endpoint(
        user: UserCtx = Depends(security.require_viewer),
    ) -> dict[str, Any]:
        return {"role": [role.value for role in user.roles]}

    @app.get("/admin")
    async def admin_endpoint(
        user: UserCtx = Depends(security.require_admin),
    ) -> dict[str, Any]:
        return {"role": [role.value for role in user.roles]}

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    with TestClient(app) as client:
        viewer_limit = parse_rate_limit(settings.RATE_LIMIT_VIEWER)[0]
        for idx in range(viewer_limit + 1):
            response = client.get("/viewer", headers=_auth_header("viewer"))
            if idx < viewer_limit:
                assert response.status_code == 200
            else:
                assert response.status_code == 429

        call_count_before = len(call_log)
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert len(call_log) == call_count_before

        for _ in range(viewer_limit + 1):
            admin_response = client.get("/admin", headers=_auth_header("admin"))
            assert admin_response.status_code == 200

    viewer_key = ("user:viewer", parse_rate_limit(settings.RATE_LIMIT_VIEWER)[1])
    admin_key = ("user:admin", parse_rate_limit(settings.RATE_LIMIT_ADMIN)[1])
    assert counters[viewer_key] == viewer_limit + 1
    assert counters[admin_key] == viewer_limit + 1
