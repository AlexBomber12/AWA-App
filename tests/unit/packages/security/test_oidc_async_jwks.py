from __future__ import annotations

import asyncio
import time
from typing import Any

import pytest
import respx
from authlib.jose import JsonWebKey, JsonWebToken
from httpx import Response

from awa_common.security import oidc
from awa_common.settings import settings

pytestmark = pytest.mark.anyio


def _generate_token(key: JsonWebKey, kid: str, issuer: str, audience: str) -> str:
    now = int(time.time())
    payload = {
        "sub": "abc",
        "iss": issuer,
        "aud": audience,
        "exp": now + 600,
        "iat": now,
        "roles": ["viewer"],
    }
    jwt = JsonWebToken(["RS256"])
    header = {"alg": "RS256", "kid": kid}
    return jwt.encode(header, payload, key).decode("utf-8")


@pytest.fixture(autouse=True)
def _enable_background_refresh(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "OIDC_JWKS_BACKGROUND_REFRESH", True, raising=False)
    monkeypatch.setenv("OIDC_JWKS_BACKGROUND_REFRESH", "1")


@pytest.fixture
def issuer_settings(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    issuer = "https://auth.example/realms/awa"
    jwks_url = f"{issuer}/protocol/openid-connect/certs"
    monkeypatch.setattr(settings, "OIDC_ISSUER", issuer)
    monkeypatch.setattr(settings, "OIDC_AUDIENCE", "awa-webapp")
    monkeypatch.setattr(settings, "OIDC_JWKS_URL", jwks_url)
    monkeypatch.setattr(settings, "OIDC_JWKS_TTL_SECONDS", 1)
    monkeypatch.setattr(settings, "OIDC_JWKS_STALE_GRACE_SECONDS", 1)
    monkeypatch.setattr(settings, "OIDC_JWKS_TIMEOUT_TOTAL_S", 5.0)
    monkeypatch.setattr(settings, "OIDC_JWKS_POOL_LIMIT", 2)
    return {"issuer": issuer, "jwks_url": jwks_url}


async def _make_provider() -> oidc.AsyncJwksProvider:
    provider = oidc.AsyncJwksProvider(cfg=settings)
    provider.start()
    return provider


@respx.mock
@pytest.mark.anyio
async def test_async_provider_fetches_jwks(issuer_settings):
    key = JsonWebKey.generate_key("RSA", 2048, is_private=True)
    public = key.as_dict(is_private=False)
    public["kid"] = "kid-1"
    respx.get(issuer_settings["jwks_url"]).mock(return_value=Response(200, json={"keys": [public]}))

    provider = await _make_provider()
    try:
        entry = await provider.get_entry(settings)
        assert "kid-1" in entry.keys_by_kid
    finally:
        await provider.close()


@respx.mock
@pytest.mark.anyio
async def test_async_provider_honors_etag(issuer_settings, monkeypatch):
    key = JsonWebKey.generate_key("RSA", 2048, is_private=True)
    public = key.as_dict(is_private=False)
    public["kid"] = "kid-1"
    route = respx.get(issuer_settings["jwks_url"])
    route.mock(
        side_effect=[
            Response(200, headers={"ETag": "v1"}, json={"keys": [public]}),
            Response(304),
        ]
    )
    provider = await _make_provider()
    provider._ttl = 1  # type: ignore[attr-defined]
    try:
        entry = await provider.get_entry(settings)
        cached = provider._cache[_issuer_from_settings()]  # type: ignore[attr-defined]
        cached.fetched_at -= 2
        refreshed = await provider.get_entry(settings)
        assert refreshed.key_set is entry.key_set
    finally:
        await provider.close()


def _issuer_from_settings() -> str:
    return (settings.OIDC_ISSUER or "").rstrip("/")


@respx.mock
@pytest.mark.anyio
async def test_stale_while_revalidate_serves_stale_then_refreshes(issuer_settings):
    key = JsonWebKey.generate_key("RSA", 2048, is_private=True)
    public = key.as_dict(is_private=False)
    public["kid"] = "kid-1"
    route = respx.get(issuer_settings["jwks_url"])
    route.mock(
        side_effect=[
            Response(200, json={"keys": [public]}),
            Response(200, json={"keys": [public]}),
        ]
    )
    provider = await _make_provider()
    provider._ttl = 1  # type: ignore[attr-defined]
    provider._stale_grace = 1  # type: ignore[attr-defined]
    try:
        entry = await provider.get_entry(settings)
        cached = provider._cache[_issuer_from_settings()]  # type: ignore[attr-defined]
        cached.fetched_at -= 1.05  # beyond TTL but within grace
        stale_entry = await provider.get_entry(settings)
        assert stale_entry is entry
        pending = provider._pending_refresh.get(_issuer_from_settings())  # type: ignore[attr-defined]
        assert pending is not None
        await asyncio.wait_for(pending, timeout=2)
        assert route.call_count >= 2
    finally:
        await provider.close()


@respx.mock
@pytest.mark.anyio
async def test_provider_raises_when_refresh_fails(issuer_settings):
    respx.get(issuer_settings["jwks_url"]).mock(return_value=Response(500))
    provider = oidc.AsyncJwksProvider(cfg=settings)
    with pytest.raises(oidc.OIDCJwksUnavailableError):
        await provider.get_entry(settings)
    await provider.close()


@respx.mock
@pytest.mark.anyio
async def test_validate_access_token_fast_path(issuer_settings):
    key = JsonWebKey.generate_key("RSA", 2048, is_private=True)
    public = key.as_dict(is_private=False)
    public["kid"] = "kid-1"
    respx.get(issuer_settings["jwks_url"]).mock(return_value=Response(200, json={"keys": [public]}))
    provider = await _make_provider()
    token = _generate_token(key, "kid-1", issuer_settings["issuer"], settings.OIDC_AUDIENCE)
    try:
        await provider.get_entry(settings)
        await asyncio.wait_for(oidc.validate_access_token(token, cfg=settings, provider=provider), timeout=0.2)
    finally:
        await provider.close()
