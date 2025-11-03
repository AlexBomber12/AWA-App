from __future__ import annotations

import base64
import json
import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Awaitable, Callable, Iterable, Mapping, cast

import httpx
from awa_common.settings import settings
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

logger = logging.getLogger(__name__)

_basic_security = HTTPBasic()


@dataclass(frozen=True, slots=True)
class Principal:
    id: str
    email: str | None
    roles: set[str]

    @classmethod
    def anonymous(cls) -> Principal:
        roles = settings.configured_roles() or {"admin", "ops", "viewer"}
        return cls(id="anonymous", email=None, roles=set(roles))


class AuthValidationError(Exception):
    """Raised when a credential cannot be validated."""


def _load_authlib() -> tuple[Any, Any]:
    """Import JOSE tools on demand; avoid hard dependency when AUTH_MODE!='oidc'."""
    try:
        from authlib.jose import JsonWebKey, JsonWebToken
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("authlib is required for OIDC mode") from exc
    return JsonWebKey, JsonWebToken


def require_basic_auth(
    credentials: HTTPBasicCredentials = Depends(_basic_security),
) -> None:
    user = os.getenv("API_BASIC_USER", "admin")
    password = os.getenv("API_BASIC_PASS", "admin")
    if not (credentials and credentials.username == user and credentials.password == password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )


def _split_csv(value: str | None) -> set[str]:
    if not value:
        return set()
    return {item.strip() for item in value.split(",") if item.strip()}


def _extract_external_groups(claims: Mapping[str, Any]) -> set[str]:
    groups: set[str] = set()
    for key in ("roles", "role", "groups", "group"):
        value = claims.get(key)
        if isinstance(value, str):
            groups.add(value)
        elif isinstance(value, Iterable):
            groups.update(str(item) for item in value)
    realm_access = claims.get("realm_access")
    if isinstance(realm_access, Mapping):
        value = realm_access.get("roles")
        if isinstance(value, Iterable):
            groups.update(str(item) for item in value)
    resource_access = claims.get("resource_access")
    if isinstance(resource_access, Mapping):
        for client in resource_access.values():
            if isinstance(client, Mapping):
                value = client.get("roles")
                if isinstance(value, Iterable):
                    groups.update(str(item) for item in value)
    cognito_groups = claims.get("cognito:groups")
    if isinstance(cognito_groups, Iterable):
        groups.update(str(item) for item in cognito_groups)
    return groups


def _expected_audiences() -> set[str]:
    audiences: set[str] = set()
    if settings.OIDC_AUDIENCE:
        audiences.add(settings.OIDC_AUDIENCE)
    if settings.OIDC_CLIENT_ID:
        audiences.add(settings.OIDC_CLIENT_ID)
    return audiences


def _get_algorithms() -> list[str]:
    algs = [alg.strip() for alg in (settings.OIDC_ALGS or "").split(",") if alg.strip()]
    return algs or ["RS256"]


def _http_get_json(url: str) -> dict[str, Any]:
    with httpx.Client(timeout=5.0) as client:
        response = client.get(url)
        response.raise_for_status()
        return cast(dict[str, Any], response.json())


def _discover_jwks_url(issuer: str) -> str:
    config_url = issuer.rstrip("/") + "/.well-known/openid-configuration"
    doc = _http_get_json(config_url)
    jwks_uri = doc.get("jwks_uri")
    if not isinstance(jwks_uri, str):
        raise AuthValidationError("OIDC discovery document missing jwks_uri")
    return jwks_uri


@lru_cache(maxsize=8)
def _load_jwks(issuer: str, jwks_url: str | None) -> Any:
    JsonWebKey, _ = _load_authlib()
    if not issuer:
        raise AuthValidationError("OIDC issuer not configured")
    url = jwks_url or _discover_jwks_url(issuer)
    data = _http_get_json(url)
    if not isinstance(data, Mapping):
        raise AuthValidationError("JWKS payload is invalid")
    return JsonWebKey.import_key_set(data)


def _from_forward_auth(headers: Mapping[str, str]) -> Principal | None:
    user = headers.get(settings.FA_USER_HEADER)
    if not user:
        return None
    email = headers.get(settings.FA_EMAIL_HEADER)
    groups_header = headers.get(settings.FA_GROUPS_HEADER)
    groups = _split_csv(groups_header)
    roles = settings.resolve_role_set(groups)
    return Principal(id=user, email=email, roles=roles)


def _from_bearer_jwt(token: str) -> Principal | None:
    JsonWebKey, JsonWebToken = _load_authlib()
    issuer = settings.OIDC_ISSUER
    if not issuer:
        raise AuthValidationError("OIDC issuer is not configured")
    jwks = _load_jwks(issuer, settings.OIDC_JWKS_URL)
    jwt_ = JsonWebToken(_get_algorithms())
    try:
        header_segment, _, _ = token.partition(".")
        padded = header_segment + "=" * (-len(header_segment) % 4)
        header_json = base64.urlsafe_b64decode(padded)
        header = json.loads(header_json)
    except Exception as exc:
        raise AuthValidationError("Invalid token header") from exc
    kid = header.get("kid")
    key = jwks.find_by_kid(kid) if kid else None
    if key is None:
        # fallback to first key for single-key sets
        keys = list(jwks)
        key = keys[0] if keys else None
    if key is None:
        raise AuthValidationError("Signing key not found for token")
    audiences = _expected_audiences()
    options: dict[str, Any] = {
        "iss": {"essential": True, "values": [issuer]},
        "exp": {"essential": True},
        "nbf": {"essential": False},
    }
    if audiences:
        options["aud"] = {"essential": True, "values": list(audiences)}
    try:
        claims = jwt_.decode(token, key, claims_options=options)
        claims.validate()
    except Exception as exc:
        raise AuthValidationError("Token validation failed") from exc
    subject = claims.get("sub")
    if not isinstance(subject, str):
        raise AuthValidationError("Token missing subject")
    email = claims.get("email")
    if not isinstance(email, str):
        email = None
    groups = _extract_external_groups(claims)
    roles = settings.resolve_role_set(groups)
    return Principal(id=subject, email=email, roles=roles)


async def get_principal(request: Request) -> Principal | None:
    mode = settings.AUTH_MODE
    if mode == "disabled":
        return None
    if mode == "forward-auth":
        return _from_forward_auth(request.headers)
    if mode == "oidc":
        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        if not auth_header:
            return None
        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unsupported authorization scheme",
            )
        token = token.strip()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing token",
            )
        try:
            return _from_bearer_jwt(token)
        except AuthValidationError as exc:
            logger.debug("oidc_token_invalid %s", exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            ) from exc
    return None


def require_roles(*allowed: str) -> Callable[..., Awaitable[Principal]]:
    allowed_set = {role for role in allowed if role}

    async def dependency(
        request: Request, principal: Principal | None = Depends(get_principal)
    ) -> Principal:
        should_protect = settings.should_protect_path(request.url.path)
        if settings.AUTH_MODE == "disabled" or not should_protect:
            fallback = principal or Principal.anonymous()
            request.state.principal = fallback
            return fallback
        if principal is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        if allowed_set and not (principal.roles & allowed_set):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        if not principal.roles and allowed_set:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        request.state.principal = principal
        return principal

    return dependency


require_viewer = require_roles("viewer")
require_ops = require_roles("ops", "admin")
require_admin = require_roles("admin")


__all__ = [
    "Principal",
    "AuthValidationError",
    "get_principal",
    "require_roles",
    "require_viewer",
    "require_ops",
    "require_admin",
    "require_basic_auth",
    "_from_forward_auth",
    "_from_bearer_jwt",
]
