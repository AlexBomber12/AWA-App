from __future__ import annotations

import time
from typing import Any

import pytest
from authlib.jose import JsonWebKey, JsonWebToken

from awa_common.security import oidc
from awa_common.security.models import Role
from awa_common.settings import settings

pytestmark = pytest.mark.anyio


class _StaticProvider:
    def __init__(self, entry: oidc._JWKSCacheEntry) -> None:
        self.entry = entry
        self.calls = 0

    async def get_entry(self, cfg: Any | None = None) -> oidc._JWKSCacheEntry:
        self.calls += 1
        return self.entry

    async def force_refresh(self, issuer: str, cfg: Any | None = None) -> oidc._JWKSCacheEntry:
        return self.entry


def _generate_key(kid: str) -> JsonWebKey:
    base = JsonWebKey.generate_key("RSA", 2048, is_private=True)
    payload = base.as_dict(is_private=True)
    payload["kid"] = kid
    return JsonWebKey.import_key(payload)


def _public_jwk(key: JsonWebKey, kid: str) -> dict[str, Any]:
    public = key.as_dict(is_private=False)
    public["kid"] = kid
    return public


@pytest.fixture
def signing_key() -> dict[str, Any]:
    issuer = "https://auth.example/realms/awa"
    audience = "awa-webapp"
    key = _generate_key("kid-1")
    jwks_url = f"{issuer}/protocol/openid-connect/certs"
    settings.OIDC_ISSUER = issuer
    settings.OIDC_AUDIENCE = audience
    settings.OIDC_JWKS_URL = jwks_url
    settings.OIDC_JWKS_TTL_SECONDS = 300
    return {
        "issuer": issuer,
        "audience": audience,
        "key": key,
        "public": _public_jwk(key, "kid-1"),
        "jwks_url": jwks_url,
    }


@pytest.fixture
def static_provider(signing_key: dict[str, Any]) -> _StaticProvider:
    key_set = JsonWebKey.import_key_set({"keys": [signing_key["public"]]})
    keys_by_kid = {"kid-1": key_set.keys[0]}
    entry = oidc._JWKSCacheEntry(  # type: ignore[attr-defined]
        issuer=signing_key["issuer"],
        jwks_uri=signing_key["jwks_url"],
        fetched_at=time.time(),
        key_set=key_set,
        keys_by_kid=keys_by_kid,
        etag="etag-1",
    )
    return _StaticProvider(entry)


def _make_token(payload: dict[str, Any], key, kid: str = "kid-1") -> str:
    jwt = JsonWebToken(["RS256"])
    header = {"alg": "RS256", "kid": kid}
    return jwt.encode(header, payload, key).decode("utf-8")


def _base_payload(issuer: str, audience: str, **extra: Any) -> dict[str, Any]:
    now = int(time.time())
    payload = {
        "sub": "user-123",
        "iss": issuer,
        "aud": audience,
        "exp": now + 600,
        "iat": now,
    }
    payload.update(extra)
    return payload


async def test_validate_access_token_returns_user(static_provider, signing_key):
    payload = _base_payload(signing_key["issuer"], signing_key["audience"], roles=["viewer"])
    token = _make_token(payload, signing_key["key"])

    user = await oidc.validate_access_token(token, cfg=settings, provider=static_provider)
    assert user.sub == "user-123"
    assert static_provider.calls == 1


async def test_roles_claim_parsed(static_provider, signing_key):
    payload = _base_payload(signing_key["issuer"], signing_key["audience"], roles=["viewer", "ops"])
    token = _make_token(payload, signing_key["key"])

    user = await oidc.validate_access_token(token, cfg=settings, provider=static_provider)
    assert user.role_set == {Role.viewer, Role.ops}


async def test_realm_access_fallback(static_provider, signing_key):
    payload = _base_payload(
        signing_key["issuer"],
        signing_key["audience"],
        realm_access={"roles": ["ops"]},
    )
    token = _make_token(payload, signing_key["key"])

    user = await oidc.validate_access_token(token, cfg=settings, provider=static_provider)
    assert user.role_set == {Role.ops}


async def test_resource_access_fallback(static_provider, signing_key):
    payload = _base_payload(
        signing_key["issuer"],
        signing_key["audience"],
        resource_access={
            signing_key["audience"]: {"roles": ["admin"]},
        },
    )
    token = _make_token(payload, signing_key["key"])

    user = await oidc.validate_access_token(token, cfg=settings, provider=static_provider)
    assert user.role_set == {Role.admin}


async def test_invalid_signature_raises(static_provider, signing_key):
    other_key = _generate_key("kid-x")
    payload = _base_payload(signing_key["issuer"], signing_key["audience"], roles=["viewer"])
    token = _make_token(payload, other_key, kid="kid-x")

    with pytest.raises(oidc.OIDCValidationError):
        await oidc.validate_access_token(token, cfg=settings, provider=static_provider)


async def test_wrong_issuer_rejected(static_provider, signing_key):
    payload = _base_payload("https://wrong/issuer", signing_key["audience"], roles=["viewer"])
    token = _make_token(payload, signing_key["key"])

    with pytest.raises(oidc.OIDCValidationError):
        await oidc.validate_access_token(token, cfg=settings, provider=static_provider)


async def test_wrong_audience_rejected(static_provider, signing_key):
    payload = _base_payload(signing_key["issuer"], "other-app", roles=["viewer"])
    token = _make_token(payload, signing_key["key"])

    with pytest.raises(oidc.OIDCValidationError):
        await oidc.validate_access_token(token, cfg=settings, provider=static_provider)


async def test_expired_token_rejected(static_provider, signing_key):
    now = int(time.time()) - 120
    payload = {
        "sub": "user-123",
        "iss": signing_key["issuer"],
        "aud": signing_key["audience"],
        "exp": now,
        "iat": now - 60,
        "roles": ["viewer"],
    }
    token = _make_token(payload, signing_key["key"])

    with pytest.raises(oidc.OIDCValidationError):
        await oidc.validate_access_token(token, cfg=settings, provider=static_provider)
