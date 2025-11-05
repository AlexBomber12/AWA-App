from __future__ import annotations

import base64
import json
import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

import httpx
from authlib.jose import JsonWebKey, JsonWebToken

from awa_common.settings import Settings, settings

from .models import Role, UserCtx

logger = logging.getLogger(__name__)

_JWT = JsonWebToken(["RS256", "PS256"])


class OIDCValidationError(Exception):
    """Raised when an incoming access token cannot be validated."""


@dataclass
class _JWKSCacheEntry:
    uri: str
    fetched_at: float
    key_set: Any
    keys_by_kid: dict[str | None, Any]


_JWKS_CACHE: dict[str, _JWKSCacheEntry] = {}
_CACHE_LOCK = threading.Lock()


def _http_get_json(url: str) -> dict[str, Any]:
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as exc:  # pragma: no cover - network failure guarded by tests
        raise OIDCValidationError(f"Failed to fetch {url}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise OIDCValidationError(f"Response from {url} is not a JSON object")
    return dict(payload)


def _discover_jwks_uri(cfg: Settings) -> str:
    issuer = (cfg.OIDC_ISSUER or "").rstrip("/")
    if not issuer:
        raise OIDCValidationError("OIDC issuer is not configured")
    discovery_url = f"{issuer}/.well-known/openid-configuration"
    document = _http_get_json(discovery_url)
    jwks_uri = document.get("jwks_uri")
    if not isinstance(jwks_uri, str) or not jwks_uri:
        raise OIDCValidationError("OIDC discovery document missing jwks_uri")
    return jwks_uri


def _import_key_set(uri: str) -> _JWKSCacheEntry:
    data = _http_get_json(uri)
    try:
        key_set = JsonWebKey.import_key_set(data)
    except Exception as exc:  # pragma: no cover - defensive against malformed JWKS
        raise OIDCValidationError("Unable to parse JWKS payload") from exc
    keys_by_kid: dict[str | None, Any] = {}
    for key in key_set.keys:
        kid = getattr(key, "kid", None)
        keys_by_kid[str(kid) if kid is not None else None] = key
    return _JWKSCacheEntry(
        uri=uri, fetched_at=time.time(), key_set=key_set, keys_by_kid=keys_by_kid
    )


def _get_jwks_entry(cfg: Settings) -> _JWKSCacheEntry:
    uri = (cfg.OIDC_JWKS_URL or "").strip() or _discover_jwks_uri(cfg)
    ttl = max(int(cfg.OIDC_JWKS_TTL_SECONDS or 0), 60)
    with _CACHE_LOCK:
        entry = _JWKS_CACHE.get(uri)
        now = time.time()
        if entry is None or now - entry.fetched_at > ttl:
            reason = "ttl_expired" if entry is not None else "cache_miss"
            logger.debug("jwks_refresh uri=%s reason=%s", uri, reason)
            entry = _import_key_set(uri)
            _JWKS_CACHE[uri] = entry
        return entry


def _decode_header(token: str) -> dict[str, Any]:
    segment, _, _ = token.partition(".")
    if not segment:
        raise OIDCValidationError("Malformed JWT token")
    padded = segment + "=" * (-len(segment) % 4)
    try:
        raw = base64.urlsafe_b64decode(padded.encode("utf-8"))
        header = json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise OIDCValidationError("Unable to decode JWT header") from exc
    if not isinstance(header, Mapping):
        raise OIDCValidationError("JWT header must be an object")
    return dict(header)


def _select_key(entry: _JWKSCacheEntry, kid: str | None, cfg: Settings) -> Any:
    key = entry.keys_by_kid.get(kid)
    if key is not None:
        return key

    # If the key is missing, force a refresh once and retry.
    with _CACHE_LOCK:
        refreshed = _import_key_set(entry.uri)
        _JWKS_CACHE[entry.uri] = refreshed
        key = refreshed.keys_by_kid.get(kid)
        if key is not None:
            logger.debug("jwks_refresh_miss_resolved uri=%s kid=%s", entry.uri, kid)
            return key
        entry = refreshed

    if kid is None and entry.keys_by_kid:
        # Some issuers omit kid when only one key exists – pick the sole key.
        return next(iter(entry.keys_by_kid.values()))
    logger.warning("jwks_key_missing uri=%s kid=%s", entry.uri, kid)
    raise OIDCValidationError("Signing key for token not found")


def _claims_options(cfg: Settings) -> dict[str, Any]:
    issuer = (cfg.OIDC_ISSUER or "").rstrip("/")
    if not issuer:
        raise OIDCValidationError("OIDC issuer is not configured")
    options: dict[str, Any] = {
        "iss": {"essential": True, "value": issuer},
        "exp": {"essential": True},
        "nbf": {"essential": False},
    }
    audience = (cfg.OIDC_AUDIENCE or "").strip()
    if audience:
        options["aud"] = {"essential": True, "values": [audience]}
    return options


def _validate_iat(claims: Mapping[str, Any]) -> None:
    value = claims.get("iat")
    if value is None:
        return
    if not isinstance(value, int | float):
        raise OIDCValidationError("iat claim must be numeric")
    now = time.time()
    # Allow up to 24 hours drift which covers most cache/token scenarios.
    if value > now + 300:
        raise OIDCValidationError("iat claim is in the future")
    if now - value > 86400:
        raise OIDCValidationError("iat claim is too old")


def _extract_email(claims: Mapping[str, Any]) -> str | None:
    email = claims.get("email")
    if isinstance(email, str) and email:
        return email
    preferred = claims.get("preferred_username")
    if isinstance(preferred, str) and preferred:
        return preferred
    return None


def _coerce_str_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable):
        result: list[str] = []
        for item in value:
            if isinstance(item, str):
                result.append(item)
            else:
                result.append(str(item))
        return result
    return []


def _extract_roles(claims: Mapping[str, Any], audience: str) -> list[Role]:
    roles_claim = claims.get("roles")
    roles: list[str] = _coerce_str_list(roles_claim)
    if roles:
        return [role for item in roles if (role := Role.from_claim(item))]

    realm_access = claims.get("realm_access")
    if isinstance(realm_access, Mapping):
        realm_roles = _coerce_str_list(realm_access.get("roles"))
        if realm_roles:
            return [role for item in realm_roles if (role := Role.from_claim(item))]

    resource_access = claims.get("resource_access")
    if isinstance(resource_access, Mapping):
        client = resource_access.get(audience)
        if isinstance(client, Mapping):
            client_roles = _coerce_str_list(client.get("roles"))
            if client_roles:
                return [role for item in client_roles if (role := Role.from_claim(item))]
    return []


def validate_access_token(
    token: str,
    *,
    cfg: Settings | None = None,
) -> UserCtx:
    """Validate an access token and return the extracted user context."""
    if not token:
        raise OIDCValidationError("Bearer token missing")

    cfg = cfg or settings
    entry = _get_jwks_entry(cfg)
    header = _decode_header(token)
    kid = header.get("kid")
    key = _select_key(entry, kid, cfg)

    options = _claims_options(cfg)
    try:
        claims = _JWT.decode(token, key, claims_options=options)
        claims.validate(leeway=30)
    except Exception as exc:
        raise OIDCValidationError("Token validation failed") from exc

    payload = dict(claims)
    _validate_iat(payload)

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise OIDCValidationError("Token missing subject")

    email = _extract_email(payload)
    audience = (cfg.OIDC_AUDIENCE or "").strip()
    roles = _extract_roles(payload, audience)

    return UserCtx(sub=subject, email=email, roles=roles, raw_claims=payload)


__all__ = ["OIDCValidationError", "validate_access_token"]
