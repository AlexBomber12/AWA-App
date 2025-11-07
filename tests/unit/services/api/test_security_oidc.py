from __future__ import annotations

import time
from typing import Any

import pytest
from authlib.jose import JsonWebKey, JsonWebToken

from awa_common.security import oidc
from awa_common.security.models import Role
from awa_common.settings import settings


def _generate_key(kid: str) -> JsonWebKey:
    base = JsonWebKey.generate_key("RSA", 2048, is_private=True)
    payload = base.as_dict(is_private=True)
    payload["kid"] = kid
    return JsonWebKey.import_key(payload)


def _public_jwk(key: JsonWebKey, kid: str) -> dict[str, Any]:
    public = key.as_dict(is_private=False)
    public["kid"] = kid
    return public


@pytest.fixture(autouse=True)
def _reset_jwks_cache(monkeypatch: pytest.MonkeyPatch):
    oidc._JWKS_CACHE.clear()  # type: ignore[attr-defined]
    yield
    oidc._JWKS_CACHE.clear()  # type: ignore[attr-defined]


@pytest.fixture
def signing_key(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    issuer = "https://auth.example/realms/awa"
    audience = "awa-webapp"
    key = _generate_key("kid-1")
    public = _public_jwk(key, "kid-1")
    jwks_url = f"{issuer}/protocol/openid-connect/certs"
    discovery_url = f"{issuer}/.well-known/openid-configuration"

    responses = {
        discovery_url: {"jwks_uri": jwks_url},
        jwks_url: {"keys": [public]},
    }
    calls: list[str] = []

    def fake_http_get(url: str) -> dict[str, Any]:
        calls.append(url)
        return responses[url]

    monkeypatch.setattr(oidc, "_http_get_json", fake_http_get)
    settings.OIDC_ISSUER = issuer
    settings.OIDC_AUDIENCE = audience
    settings.OIDC_JWKS_URL = None
    settings.OIDC_JWKS_TTL_SECONDS = 900

    return {
        "issuer": issuer,
        "audience": audience,
        "key": key,
        "calls": calls,
        "jwks_url": jwks_url,
        "discovery_url": discovery_url,
    }


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


def test_validate_access_token_caches_jwks(signing_key):
    payload = _base_payload(signing_key["issuer"], signing_key["audience"], roles=["viewer"])
    token = _make_token(payload, signing_key["key"])

    user = oidc.validate_access_token(token, cfg=settings)
    assert user.sub == "user-123"
    assert signing_key["calls"].count(signing_key["jwks_url"]) == 1

    # Second call should hit the cache (no additional JWKS fetch).
    oidc.validate_access_token(token, cfg=settings)
    assert signing_key["calls"].count(signing_key["jwks_url"]) == 1


def test_roles_claim_parsed(signing_key):
    payload = _base_payload(signing_key["issuer"], signing_key["audience"], roles=["viewer", "ops"])
    token = _make_token(payload, signing_key["key"])

    user = oidc.validate_access_token(token, cfg=settings)
    assert user.role_set == {Role.viewer, Role.ops}


def test_realm_access_fallback(signing_key):
    payload = _base_payload(
        signing_key["issuer"],
        signing_key["audience"],
        realm_access={"roles": ["ops"]},
    )
    token = _make_token(payload, signing_key["key"])

    user = oidc.validate_access_token(token, cfg=settings)
    assert user.role_set == {Role.ops}


def test_resource_access_fallback(signing_key):
    payload = _base_payload(
        signing_key["issuer"],
        signing_key["audience"],
        resource_access={
            signing_key["audience"]: {"roles": ["admin"]},
        },
    )
    token = _make_token(payload, signing_key["key"])

    user = oidc.validate_access_token(token, cfg=settings)
    assert user.role_set == {Role.admin}


def test_invalid_signature_raises(monkeypatch: pytest.MonkeyPatch, signing_key):
    other_key = _generate_key("kid-x")
    payload = _base_payload(signing_key["issuer"], signing_key["audience"], roles=["viewer"])
    token = _make_token(payload, other_key, kid="kid-x")

    with pytest.raises(oidc.OIDCValidationError):
        oidc.validate_access_token(token, cfg=settings)


def test_wrong_issuer_rejected(signing_key):
    payload = _base_payload("https://wrong/issuer", signing_key["audience"], roles=["viewer"])
    token = _make_token(payload, signing_key["key"])

    with pytest.raises(oidc.OIDCValidationError):
        oidc.validate_access_token(token, cfg=settings)


def test_wrong_audience_rejected(signing_key):
    payload = _base_payload(signing_key["issuer"], "other-app", roles=["viewer"])
    token = _make_token(payload, signing_key["key"])

    with pytest.raises(oidc.OIDCValidationError):
        oidc.validate_access_token(token, cfg=settings)


def test_expired_token_rejected(signing_key):
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
        oidc.validate_access_token(token, cfg=settings)
