from __future__ import annotations

import asyncio
import base64
import contextlib
import json
import os
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

import httpx
import structlog
from authlib.jose import JsonWebKey, JsonWebToken

from awa_common.http_client import AsyncHTTPClient
from awa_common.metrics import record_oidc_jwks_refresh, record_oidc_validation_failure
from awa_common.settings import Settings, settings

from .models import Role, UserCtx

logger = structlog.get_logger(__name__)

_JWT = JsonWebToken(["RS256", "PS256"])


class _JSONHTTPClientWrapper:
    def __init__(self, client: Any):
        self._client = client

    async def get(self, url: str, **kwargs: Any):
        kwargs.pop("allowed_statuses", None)
        return await self._client.get(url, **kwargs)

    async def get_json(self, url: str, **kwargs: Any):
        kwargs.pop("allowed_statuses", None)
        response = await self._client.get(url, **kwargs)
        try:
            return response.json()
        finally:
            close = getattr(response, "aclose", None)
            if callable(close):
                await close()
            elif hasattr(response, "close"):
                response.close()

    async def aclose(self) -> None:
        close = getattr(self._client, "aclose", None)
        if callable(close):
            await close()


def _suppress_cancelled(task: asyncio.Task[Any]) -> None:
    with contextlib.suppress(asyncio.CancelledError):
        task.result()


class OIDCValidationError(Exception):
    """Raised when an incoming access token cannot be validated."""


class OIDCJwksUnavailableError(OIDCValidationError):
    """Raised when JWKS keys cannot be obtained or refreshed."""


@dataclass
class _JWKSCacheEntry:
    issuer: str
    jwks_uri: str
    fetched_at: float
    key_set: Any
    keys_by_kid: dict[str | None, Any]
    etag: str | None = None

    @property
    def age(self) -> float:
        return max(time.time() - self.fetched_at, 0.0)


class AsyncJwksProvider:
    """Async JWKS provider with TTL cache and stale-while-revalidate semantics."""

    def __init__(
        self, cfg: Settings | None = None, *, client: AsyncHTTPClient | httpx.AsyncClient | None = None
    ) -> None:
        self._cfg_default = cfg or settings
        self._ttl = max(int(self._cfg_default.OIDC_JWKS_TTL_SECONDS or 0), 60)
        self._stale_grace = max(int(self._cfg_default.OIDC_JWKS_STALE_GRACE_SECONDS or 0), 0)
        timeout = httpx.Timeout(
            float(self._cfg_default.OIDC_JWKS_TIMEOUT_TOTAL_S or 5.0),
            connect=float(self._cfg_default.OIDC_JWKS_TIMEOUT_CONNECT_S or 2.0),
            read=float(self._cfg_default.OIDC_JWKS_TIMEOUT_READ_S or 2.0),
        )
        pool = max(int(self._cfg_default.OIDC_JWKS_POOL_LIMIT or 1), 1)
        limits = httpx.Limits(max_connections=pool, max_keepalive_connections=pool)
        max_retries = max(int(getattr(self._cfg_default, "OIDC_JWKS_MAX_RETRIES", 1) or 1), 1)
        base_client = client or AsyncHTTPClient(
            integration="oidc_jwks",
            timeout=timeout,
            limits=limits,
            total_timeout_s=float(self._cfg_default.OIDC_JWKS_TIMEOUT_TOTAL_S or 5.0),
            max_retries=max_retries,
        )
        if not hasattr(base_client, "get_json"):
            base_client = _JSONHTTPClientWrapper(base_client)
        self._client = base_client
        self._client_owned = client is None
        self._cache: dict[str, _JWKSCacheEntry] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._jwks_uri_cache: dict[str, str] = {}
        self._pending_refresh: dict[str, asyncio.Task[None]] = {}
        self._background_task: asyncio.Task[None] | None = None
        self._closed = False
        self._refresh_interval = max(30.0, min(float(self._ttl), 120.0))
        self._background_enabled = bool(getattr(self._cfg_default, "OIDC_JWKS_BACKGROUND_REFRESH", True))
        if getattr(self._cfg_default, "TESTING", False) or "PYTEST_CURRENT_TEST" in os.environ:
            self._background_enabled = False

    def start(self) -> None:
        if self._background_task is not None or self._closed or not self._background_enabled:
            return
        task = asyncio.create_task(self._refresh_loop())
        task.add_done_callback(_suppress_cancelled)
        self._background_task = task

    async def close(self) -> None:
        self._closed = True
        for task in list(self._pending_refresh.values()):
            task.cancel()
        if self._background_task is not None:
            self._background_task.cancel()
        await asyncio.gather(*self._pending_refresh.values(), return_exceptions=True)
        if self._background_task is not None:
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await self._background_task
        if self._client_owned:
            await self._client.aclose()
        self._pending_refresh.clear()
        self._background_task = None

    async def get_entry(self, cfg: Settings | None = None) -> _JWKSCacheEntry:
        resolved_cfg = cfg or self._cfg_default
        issuer = _issuer_from_settings(resolved_cfg)
        entry = self._cache.get(issuer)
        now = time.time()
        if entry and not self._is_expired(entry, now):
            record_oidc_jwks_refresh(issuer, success=True, age_seconds=entry.age, count=False)
            return entry
        if entry and self._is_within_grace(entry, now):
            refresh_task = asyncio.create_task(self._refresh(issuer, resolved_cfg, force=True, background=True))
            self._pending_refresh[issuer] = refresh_task
            with contextlib.suppress(Exception):
                await asyncio.wait_for(refresh_task, timeout=5.0)
            record_oidc_jwks_refresh(issuer, success=True, age_seconds=entry.age, count=False)
            return entry
        refreshed = await self._refresh(issuer, resolved_cfg, force=True, background=False)
        record_oidc_jwks_refresh(issuer, success=True, age_seconds=refreshed.age, count=False)
        return refreshed

    async def force_refresh(self, issuer: str, cfg: Settings | None = None) -> _JWKSCacheEntry:
        resolved_cfg = cfg or self._cfg_default
        refreshed = await self._refresh(issuer, resolved_cfg, force=True, background=False)
        record_oidc_jwks_refresh(issuer, success=True, age_seconds=refreshed.age, count=False)
        return refreshed

    def _schedule_refresh(self, issuer: str, cfg: Settings) -> None:
        task = self._pending_refresh.get(issuer)
        if task and not task.done():
            return

        async def _runner() -> None:
            try:
                await self._refresh(issuer, cfg, force=True, background=True)
            except Exception:  # pragma: no cover - background errors are logged already
                pass

        if not self._background_enabled:
            return
        task = asyncio.create_task(_runner())
        self._pending_refresh[issuer] = task

        def _cleanup(completed: asyncio.Task[None]) -> None:
            self._pending_refresh.pop(issuer, None)
            _suppress_cancelled(completed)

        task.add_done_callback(_cleanup)

    def _is_expired(self, entry: _JWKSCacheEntry, now: float) -> bool:
        return now - entry.fetched_at >= self._ttl

    def _is_within_grace(self, entry: _JWKSCacheEntry, now: float) -> bool:
        return now - entry.fetched_at < (self._ttl + self._stale_grace)

    async def _refresh(self, issuer: str, cfg: Settings, *, force: bool, background: bool) -> _JWKSCacheEntry:
        lock = self._locks.setdefault(issuer, asyncio.Lock())
        async with lock:
            entry = self._cache.get(issuer)
            if not force and entry and not self._is_expired(entry, time.time()):
                return entry
            jwks_uri = await self._resolve_jwks_uri(issuer, cfg)
            try:
                refreshed = await self._fetch_jwks(issuer, jwks_uri, entry)
            except OIDCJwksUnavailableError as exc:
                if background and entry is not None:
                    logger.warning("oidc_jwks_refresh_background_failed", issuer=issuer, error=str(exc))
                    return entry
                raise
            self._cache[issuer] = refreshed
            record_oidc_jwks_refresh(issuer, success=True, age_seconds=0.0)
            return refreshed

    async def _fetch_jwks(
        self,
        issuer: str,
        jwks_uri: str,
        cached: _JWKSCacheEntry | None,
    ) -> _JWKSCacheEntry:
        headers = {"Accept": "application/json"}
        if cached and cached.etag:
            headers["If-None-Match"] = cached.etag
        try:
            response = await self._client.get(jwks_uri, headers=headers, allowed_statuses=frozenset({304}))
            if response.status_code == 304 and cached is not None:
                return _JWKSCacheEntry(
                    issuer=issuer,
                    jwks_uri=jwks_uri,
                    fetched_at=time.time(),
                    key_set=cached.key_set,
                    keys_by_kid=cached.keys_by_kid,
                    etag=cached.etag,
                )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, Mapping):
                raise OIDCValidationError(f"Response from {jwks_uri} is not a JSON object")
            try:
                key_set = JsonWebKey.import_key_set(payload)
            except Exception as exc:  # pragma: no cover - defensive against malformed JWKS
                raise OIDCValidationError("Unable to parse JWKS payload") from exc
            keys_by_kid: dict[str | None, Any] = {}
            for key in key_set.keys:
                kid = getattr(key, "kid", None)
                keys_by_kid[str(kid) if kid is not None else None] = key
            etag = response.headers.get("ETag") or response.headers.get("etag")
            return _JWKSCacheEntry(
                issuer=issuer,
                jwks_uri=jwks_uri,
                fetched_at=time.time(),
                key_set=key_set,
                keys_by_kid=keys_by_kid,
                etag=etag,
            )
        except Exception as exc:  # pragma: no cover - unexpected network failure
            record_oidc_jwks_refresh(issuer, success=False)
            raise OIDCJwksUnavailableError(f"Failed to refresh JWKS for {issuer}") from exc

    async def _resolve_jwks_uri(self, issuer: str, cfg: Settings) -> str:
        override = (cfg.OIDC_JWKS_URL or "").strip()
        if override:
            self._jwks_uri_cache[issuer] = override
            return override
        cached = self._jwks_uri_cache.get(issuer)
        if cached:
            return cached
        discovery_url = f"{issuer}/.well-known/openid-configuration"
        document = await self._http_get_json(discovery_url)
        jwks_uri = document.get("jwks_uri")
        if not isinstance(jwks_uri, str) or not jwks_uri:
            raise OIDCValidationError("OIDC discovery document missing jwks_uri")
        self._jwks_uri_cache[issuer] = jwks_uri
        return jwks_uri

    async def _http_get_json(self, url: str) -> Mapping[str, Any]:
        payload = await self._client.get_json(url, headers={"Accept": "application/json"})
        if not isinstance(payload, Mapping):
            raise OIDCValidationError(f"Response from {url} is not a JSON object")
        return payload

    async def _refresh_loop(self) -> None:
        try:
            while not self._closed and self._background_enabled:
                await asyncio.sleep(self._refresh_interval)
                issuers = list(self._cache.keys())
                for issuer in issuers:
                    if self._closed:
                        return
                    try:
                        await self._refresh(issuer, self._cfg_default, force=True, background=True)
                    except Exception as exc:  # pragma: no cover - background noise
                        logger.warning("oidc_jwks_refresh_loop_failed", issuer=issuer, error=str(exc))
        except asyncio.CancelledError:  # pragma: no cover - shutdown
            return


def _issuer_from_settings(cfg: Settings) -> str:
    issuer = (cfg.OIDC_ISSUER or "").rstrip("/")
    if not issuer:
        raise OIDCValidationError("OIDC issuer is not configured")
    return issuer


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


def _claims_options(cfg: Settings) -> dict[str, Any]:
    issuer = _issuer_from_settings(cfg)
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


def _reason_from_exception(exc: Exception) -> str:
    message = str(exc).lower()
    if "expired" in message or "exp" in message:
        return "exp"
    if "audience" in message or "aud" in message:
        return "aud"
    return "signature"


async def _select_key(
    provider: AsyncJwksProvider,
    entry: _JWKSCacheEntry,
    kid: str | None,
    cfg: Settings,
) -> Any:
    key = entry.keys_by_kid.get(kid)
    if key is not None:
        return key
    refreshed = await provider.force_refresh(entry.issuer, cfg)
    key = refreshed.keys_by_kid.get(kid)
    if key is not None:
        logger.debug("oidc_jwks_refresh_miss_resolved", issuer=entry.issuer, kid=kid)
        return key
    if kid is None and refreshed.keys_by_kid:
        return next(iter(refreshed.keys_by_kid.values()))
    logger.warning("oidc_jwks_key_missing", issuer=entry.issuer, kid=kid)
    raise OIDCValidationError("Signing key for token not found")


_PROVIDER: AsyncJwksProvider | None = None
_PROVIDER_LOCK: asyncio.Lock | None = None


async def init_async_jwks_provider(cfg: Settings | None = None) -> AsyncJwksProvider:
    provider = await _get_or_create_provider(cfg or settings)
    provider.start()
    return provider


async def shutdown_async_jwks_provider() -> None:
    global _PROVIDER
    provider = _PROVIDER
    if provider is None:
        return
    _PROVIDER = None
    await provider.close()


async def _get_or_create_provider(cfg: Settings) -> AsyncJwksProvider:
    global _PROVIDER
    if _PROVIDER is not None:
        return _PROVIDER
    global _PROVIDER_LOCK
    if _PROVIDER_LOCK is None:
        _PROVIDER_LOCK = asyncio.Lock()
    async with _PROVIDER_LOCK:
        if _PROVIDER is None:
            provider = AsyncJwksProvider(cfg)
            provider.start()
            _PROVIDER = provider
    assert _PROVIDER is not None
    return _PROVIDER


async def validate_access_token(
    token: str,
    *,
    cfg: Settings | None = None,
    provider: AsyncJwksProvider | None = None,
) -> UserCtx:
    """Validate an access token and return the extracted user context."""
    if not token:
        raise OIDCValidationError("Bearer token missing")

    cfg = cfg or settings
    provider = provider or await _get_or_create_provider(cfg)
    entry = await provider.get_entry(cfg)

    header = _decode_header(token)
    kid = header.get("kid")
    key = await _select_key(provider, entry, kid, cfg)

    options = _claims_options(cfg)
    try:
        claims = _JWT.decode(token, key, claims_options=options)
        claims.validate(leeway=30)
    except Exception as exc:
        record_oidc_validation_failure(_reason_from_exception(exc))
        raise OIDCValidationError("Token validation failed") from exc

    payload = dict(claims)
    try:
        _validate_iat(payload)
    except OIDCValidationError:
        record_oidc_validation_failure("claims")
        raise

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        record_oidc_validation_failure("claims")
        raise OIDCValidationError("Token missing subject")

    email = _extract_email(payload)
    audience = (cfg.OIDC_AUDIENCE or "").strip()
    roles = _extract_roles(payload, audience)

    return UserCtx(sub=subject, email=email, roles=roles, raw_claims=payload)


__all__ = [
    "AsyncJwksProvider",
    "OIDCJwksUnavailableError",
    "OIDCValidationError",
    "init_async_jwks_provider",
    "shutdown_async_jwks_provider",
    "validate_access_token",
]
