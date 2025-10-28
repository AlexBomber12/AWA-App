from __future__ import annotations

import base64
import time
from typing import Any, Callable

import pytest
from authlib.jose import JsonWebKey
from awa_common.settings import settings
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from jose import jwt

import services.api.security as security
from services.api.audit import AuditMiddleware, insert_audit
from services.api.security import Principal, require_ops, require_viewer


class _StubSessionCtx:
    def __init__(self, sink: list[dict[str, Any]]):
        self._sink = sink
        self.executed: list[tuple[Any, Any | None]] = []
        self.committed = False

    async def __aenter__(self) -> _StubSessionCtx:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def execute(self, stmt: Any, params: Any | None = None) -> None:
        self.executed.append((stmt, params))
        self._sink.append(params or {})

    async def commit(self) -> None:
        self.committed = True


def _build_app(session_factory: Callable[[], _StubSessionCtx]) -> FastAPI:
    app = FastAPI()
    app.add_middleware(AuditMiddleware, session_factory=session_factory)

    @app.get("/_t/protected")
    async def protected_route(
        principal: Principal = Depends(require_ops),
    ) -> dict[str, Any]:
        return {"id": principal.id, "roles": sorted(principal.roles)}

    @app.get("/_t/view")
    async def viewer_route(
        principal: Principal = Depends(require_viewer),
    ) -> dict[str, Any]:
        return {"id": principal.id, "roles": sorted(principal.roles)}

    return app


def _token_headers(kid: str) -> dict[str, Any]:
    return {"kid": kid, "alg": "RS256", "typ": "JWT"}


def _issue_token(private_key_pem: bytes, kid: str, groups: list[str]) -> str:
    now = int(time.time())
    payload = {
        "iss": "https://test.example/oidc",
        "aud": "awa",
        "sub": "user-123",
        "email": "ops@example.com",
        "nbf": now - 10,
        "exp": now + 600,
        "groups": groups,
    }
    return jwt.encode(
        payload,
        private_key_pem,
        algorithm="RS256",
        headers=_token_headers(kid),
    )


def _generate_rsa_material() -> tuple[bytes, dict[str, Any]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    numbers = private_key.public_key().public_numbers()
    length = (numbers.n.bit_length() + 7) // 8
    n_bytes = numbers.n.to_bytes(length, "big")
    e_bytes = numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")
    public_jwk = {
        "kty": "RSA",
        "kid": "kid-1",
        "use": "sig",
        "alg": "RS256",
        "n": base64.urlsafe_b64encode(n_bytes).rstrip(b"=").decode("ascii"),
        "e": base64.urlsafe_b64encode(e_bytes).rstrip(b"=").decode("ascii"),
    }
    return private_pem, public_jwk


def _prepare_oidc(monkeypatch: pytest.MonkeyPatch):
    private_pem, public_jwk = _generate_rsa_material()
    jwks = JsonWebKey.import_key_set({"keys": [public_jwk]})

    security._load_jwks.cache_clear()
    monkeypatch.setattr(security, "_load_jwks", lambda *_a, **_k: jwks)

    monkeypatch.setattr(settings, "AUTH_MODE", "oidc", raising=False)
    monkeypatch.setattr(
        settings, "OIDC_ISSUER", "https://test.example/oidc", raising=False
    )
    monkeypatch.setattr(settings, "OIDC_AUDIENCE", "awa", raising=False)
    monkeypatch.setattr(settings, "OIDC_CLIENT_ID", None, raising=False)
    monkeypatch.setattr(settings, "OIDC_JWKS_URL", None, raising=False)
    monkeypatch.setattr(settings, "AUTH_REQUIRED_ROUTES_REGEX", "", raising=False)
    monkeypatch.setattr(settings, "_role_map_cache", None, raising=False)
    monkeypatch.setattr(settings, "_role_map_cache_key", None, raising=False)
    token_ok = _issue_token(private_pem, public_jwk["kid"], ["ops"])
    token_viewer = _issue_token(private_pem, public_jwk["kid"], ["viewer"])
    token_invalid = token_ok[:-4] + "abcd"
    return token_ok, token_viewer, token_invalid


def _prepare_forward_auth(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "forward-auth", raising=False)
    monkeypatch.setattr(settings, "FA_USER_HEADER", "X-Forwarded-User", raising=False)
    monkeypatch.setattr(settings, "FA_EMAIL_HEADER", "X-Forwarded-Email", raising=False)
    monkeypatch.setattr(
        settings, "FA_GROUPS_HEADER", "X-Forwarded-Groups", raising=False
    )
    monkeypatch.setattr(settings, "AUTH_REQUIRED_ROUTES_REGEX", "", raising=False)
    monkeypatch.setattr(settings, "_role_map_cache", None, raising=False)
    monkeypatch.setattr(settings, "_role_map_cache_key", None, raising=False)


@pytest.fixture
def audit_sink():
    return []


@pytest.fixture
def secured_app(audit_sink):
    def factory():
        return _StubSessionCtx(audit_sink)

    return _build_app(factory)


def test_oidc_bearer_honors_roles(
    monkeypatch: pytest.MonkeyPatch, secured_app, audit_sink
):
    token_ok, token_viewer, token_invalid = _prepare_oidc(monkeypatch)

    with TestClient(secured_app) as client:
        res = client.get(
            "/_t/protected",
            headers={"Authorization": f"Bearer {token_ok}"},
        )
        assert res.status_code == 200
        assert res.json()["roles"] == ["ops"]
        assert audit_sink, "Audit middleware should capture the request"
        audit_entry = audit_sink[-1]
        assert audit_entry["user_id"] == "user-123"
        assert audit_entry["roles"] == ["ops"]

        res_view = client.get(
            "/_t/protected",
            headers={"Authorization": f"Bearer {token_viewer}"},
        )
        assert res_view.status_code == 403

        res_invalid = client.get(
            "/_t/protected",
            headers={"Authorization": f"Bearer {token_invalid}"},
        )
        assert res_invalid.status_code == 401


def test_forward_auth_enforces_groups(
    monkeypatch: pytest.MonkeyPatch, secured_app, audit_sink
):
    _prepare_forward_auth(monkeypatch)

    with TestClient(secured_app) as client:
        res = client.get(
            "/_t/protected",
            headers={
                "X-Forwarded-User": "ops-user",
                "X-Forwarded-Email": "ops@example.com",
                "X-Forwarded-Groups": "admin,ops",
            },
        )
        assert res.status_code == 200
        assert sorted(res.json()["roles"]) == ["admin", "ops"]
        assert audit_sink, "Forward-auth request should be logged"
        res_forbidden = client.get(
            "/_t/protected",
            headers={
                "X-Forwarded-User": "view-only",
                "X-Forwarded-Groups": "viewer",
            },
        )
        assert res_forbidden.status_code == 403


def test_audit_insert_helper():
    sink: list[dict[str, Any]] = []
    session = _StubSessionCtx(sink)
    record = {
        "user_id": "user-123",
        "email": "ops@example.com",
        "roles": ["ops"],
        "method": "GET",
        "path": "/_t/protected",
        "route": "/_t/protected",
        "status": 200,
        "latency_ms": 12,
        "ip": "127.0.0.1",
        "ua": "pytest",
        "request_id": "req-1",
    }

    import asyncio

    async def _run():
        async with session:
            await insert_audit(session, record)
            await session.commit()

    asyncio.run(_run())
    assert sink
    params = sink[0]
    assert params["user_id"] == "user-123"
    assert params["roles"] == ["ops"]
