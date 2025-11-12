from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from fastapi_limiter import FastAPILimiter
from starlette.requests import Request as StarletteRequest

from awa_common.security import ratelimit
from awa_common.security.models import Role, UserCtx
from awa_common.security.ratelimit import install_role_based_rate_limit
from awa_common.settings import parse_rate_limit, settings
from services.api import security


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_role_based_rate_limiter_enforces_by_role(monkeypatch):  # noqa: C901
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


def _make_request(
    path: str = "/resource",
    headers: Mapping[str, str] | None = None,
    client: tuple[str, int] | None = None,
) -> StarletteRequest:
    header_items = []
    for key, value in (headers or {}).items():
        header_items.append((key.lower().encode("latin-1"), value.encode("latin-1")))

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": header_items,
        "query_string": b"",
        "client": client if client is not None else ("10.0.0.1", 12345),
        "server": ("test", 80),
        "scheme": "http",
    }
    return StarletteRequest(scope, receive)


def test_select_role_prioritises_admin():
    user = UserCtx(
        sub="s1",
        email=None,
        roles=[Role.viewer, Role.ops, Role.admin],
        raw_claims={},
    )
    assert ratelimit._select_role(user) is Role.admin
    assert ratelimit._select_role(None) is Role.viewer


def test_client_ip_precedence():
    request = _make_request(headers={"x-forwarded-for": "1.1.1.1, 2.2.2.2"})
    assert ratelimit._client_ip(request) == "1.1.1.1"

    request = _make_request(headers={"x-real-ip": "3.3.3.3"})
    assert ratelimit._client_ip(request) == "3.3.3.3"

    request = _make_request(client=("4.4.4.4", 0))
    assert ratelimit._client_ip(request) == "4.4.4.4"

    request = _make_request()
    request.scope["client"] = None  # type: ignore[assignment]
    assert ratelimit._client_ip(request) == "unknown"


def test_rate_limit_identifier_defaults_to_ip():
    request = _make_request()
    assert ratelimit._rate_limit_identifier(request).startswith("ip:")

    request.state.user = UserCtx(sub="abc", email=None, roles=[Role.viewer], raw_claims={})
    assert ratelimit._rate_limit_identifier(request) == "user:abc"


def test_normalize_limit_parses_various_inputs():
    cfg = SimpleNamespace(
        RATE_LIMIT_VIEWER="10/minute",
        RATE_LIMIT_OPS="20/minute",
        RATE_LIMIT_ADMIN="30/minute",
    )
    assert ratelimit._normalize_limit((5, 60), cfg.RATE_LIMIT_VIEWER) == (5, 60)
    assert ratelimit._normalize_limit([7, 1], cfg.RATE_LIMIT_VIEWER) == (7, 1)
    assert ratelimit._normalize_limit("8/sec", cfg.RATE_LIMIT_VIEWER) == (8, 1)
    with pytest.raises(ValueError):
        ratelimit._normalize_limit(123, cfg.RATE_LIMIT_VIEWER)


@pytest.mark.anyio
async def test_role_limiter_skips_health_path(monkeypatch):
    monkeypatch.setattr(FastAPILimiter, "redis", object(), raising=False)
    limiter = ratelimit.RoleBasedRateLimiter(
        settings=SimpleNamespace(
            ENV="local",
            RATE_LIMIT_VIEWER="1/minute",
            RATE_LIMIT_OPS="1/minute",
            RATE_LIMIT_ADMIN="1/minute",
        )
    )
    request = _make_request(path="/health")
    await limiter(request)


@pytest.mark.anyio
async def test_role_limiter_respects_skip_flag(monkeypatch):
    monkeypatch.setattr(FastAPILimiter, "redis", object(), raising=False)
    limiter = ratelimit.RoleBasedRateLimiter(
        settings=SimpleNamespace(
            ENV="local",
            RATE_LIMIT_VIEWER="1/minute",
            RATE_LIMIT_OPS="1/minute",
            RATE_LIMIT_ADMIN="1/minute",
        )
    )
    request = _make_request(path="/data")
    request.state.skip_rate_limit = True
    await limiter(request)


@pytest.mark.anyio
async def test_role_limiter_requires_redis_in_stage(monkeypatch):
    monkeypatch.setattr(FastAPILimiter, "redis", None, raising=False)
    limiter = ratelimit.RoleBasedRateLimiter(
        settings=SimpleNamespace(
            ENV="stage",
            RATE_LIMIT_VIEWER="1/minute",
            RATE_LIMIT_OPS="1/minute",
            RATE_LIMIT_ADMIN="1/minute",
        )
    )
    request = _make_request(path="/data")
    with pytest.raises(HTTPException) as exc_info:
        await limiter(request)
    assert exc_info.value.status_code == 503


@pytest.mark.anyio
async def test_role_limiter_warns_when_redis_missing_locally(monkeypatch):
    recorded: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    class DummyLogger:
        def warning(self, *args: Any, **kwargs: Any) -> None:
            recorded.append((args, kwargs))

    monkeypatch.setattr(ratelimit, "logger", DummyLogger())
    monkeypatch.setattr(FastAPILimiter, "redis", None, raising=False)
    limiter = ratelimit.RoleBasedRateLimiter(
        settings=SimpleNamespace(
            ENV="local",
            RATE_LIMIT_VIEWER="1/minute",
            RATE_LIMIT_OPS="1/minute",
            RATE_LIMIT_ADMIN="1/minute",
        )
    )
    request = _make_request(path="/data")
    await limiter(request)
    assert recorded, "expected warning when redis is unavailable locally"


@pytest.mark.anyio
async def test_role_limiter_handles_invalid_token(monkeypatch):
    class DummyLimiter:
        def __init__(self, **_: Any) -> None:
            self.calls = 0

        async def __call__(self, request: Request, *_, **__) -> None:
            self.calls += 1

    latest: DummyLimiter | None = None

    def limiter_factory(**kwargs: Any) -> DummyLimiter:
        nonlocal latest
        latest = DummyLimiter(**kwargs)
        return latest

    monkeypatch.setattr("awa_common.security.ratelimit.RateLimiter", limiter_factory, raising=True)
    monkeypatch.setattr(FastAPILimiter, "redis", object(), raising=False)

    async def _raise_invalid(token: str, cfg: Any) -> None:
        raise ratelimit.oidc.OIDCValidationError("invalid")

    monkeypatch.setattr(ratelimit.oidc, "validate_access_token", _raise_invalid, raising=True)
    limiter = ratelimit.RoleBasedRateLimiter(
        settings=SimpleNamespace(
            ENV="local",
            RATE_LIMIT_VIEWER="1/minute",
            RATE_LIMIT_OPS="1/minute",
            RATE_LIMIT_ADMIN="1/minute",
        )
    )
    request = _make_request(headers={"Authorization": "Bearer invalid"})
    await limiter(request)
    assert latest is not None and latest.calls == 1


@pytest.mark.anyio
async def test_role_limiter_handles_legacy_signature(monkeypatch):
    class LegacyLimiter:
        def __init__(self, **_: Any) -> None:
            self.calls = 0

        async def __call__(self, request: Request, *args: Any, **kwargs: Any) -> None:
            self.calls += 1
            if not args:
                raise TypeError("__call__() missing 1 required positional argument: 'response'")

    created: list[LegacyLimiter] = []

    def limiter_factory(**kwargs: Any) -> LegacyLimiter:
        limiter = LegacyLimiter(**kwargs)
        created.append(limiter)
        return limiter

    monkeypatch.setattr("awa_common.security.ratelimit.RateLimiter", limiter_factory, raising=True)
    monkeypatch.setattr(FastAPILimiter, "redis", object(), raising=False)
    limiter = ratelimit.RoleBasedRateLimiter(
        settings=SimpleNamespace(
            ENV="local",
            RATE_LIMIT_VIEWER="1/minute",
            RATE_LIMIT_OPS="1/minute",
            RATE_LIMIT_ADMIN="1/minute",
        )
    )
    request = _make_request(path="/legacy")
    await limiter(request)
    assert created and created[0].calls == 2


def test_no_rate_limit_decorator_sync():
    request = _make_request()

    @ratelimit.no_rate_limit
    def handler(req: StarletteRequest) -> str:
        assert getattr(req.state, "skip_rate_limit", False) is True
        return "ok"

    assert handler(request) == "ok"


@pytest.mark.anyio
async def test_no_rate_limit_decorator_async():
    request = _make_request()

    @ratelimit.no_rate_limit
    async def handler(req: StarletteRequest) -> str:
        assert getattr(req.state, "skip_rate_limit", False) is True
        return "async-ok"

    assert await handler(request) == "async-ok"
