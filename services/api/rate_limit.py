from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import structlog
from fastapi import HTTPException, Request
from fastapi_limiter import FastAPILimiter

from awa_common.metrics import record_http_429
from awa_common.security import oidc
from awa_common.security.models import Role, UserCtx
from awa_common.settings import Settings, parse_rate_limit, settings

logger = structlog.get_logger(__name__)
_DEFAULT_SKIP_PATHS = {"/ready", "/health", "/metrics"}


@dataclass(frozen=True)
class RateLimitProfile:
    name: str
    limit: int
    window: int


class SmartRateLimiter:
    def __init__(self, cfg: Settings) -> None:
        self._cfg = cfg
        self._skip_paths = set(_DEFAULT_SKIP_PATHS)
        self._role_limits: dict[Role, tuple[int, int]] = {
            Role.viewer: parse_rate_limit(cfg.RATE_LIMIT_VIEWER),
            Role.ops: parse_rate_limit(cfg.RATE_LIMIT_OPS),
            Role.admin: parse_rate_limit(cfg.RATE_LIMIT_ADMIN),
        }
        window = max(int(cfg.RATE_LIMIT_WINDOW_SECONDS or 0), 1)
        self._profiles: dict[str, RateLimitProfile] = {
            "score": RateLimitProfile(
                "score",
                max(int(cfg.RATE_LIMIT_SCORE_PER_USER or 0), 1),
                window,
            ),
            "roi_by_vendor": RateLimitProfile(
                "roi_by_vendor",
                max(int(cfg.RATE_LIMIT_ROI_BY_VENDOR_PER_USER or 0), 1),
                window,
            ),
        }

    def dependency(self, profile: RateLimitProfile | None = None) -> Callable[[Request], Awaitable[None]]:
        async def _dependency(request: Request) -> None:
            await self._enforce(request, profile)

        return _dependency

    @property
    def score_profile(self) -> RateLimitProfile:
        return self._profiles["score"]

    @property
    def roi_by_vendor_profile(self) -> RateLimitProfile:
        return self._profiles["roi_by_vendor"]

    async def _enforce(self, request: Request, profile: RateLimitProfile | None) -> None:
        if getattr(request.state, "skip_rate_limit", False):
            return
        if request.url.path in self._skip_paths:
            return

        limiter_ready = getattr(FastAPILimiter, "redis", None)
        if limiter_ready is None:
            if (self._cfg.ENV or "local").lower() in {"stage", "prod"}:
                raise HTTPException(status_code=503, detail="Rate limiter not ready")
            logger.warning("rate_limiter_not_initialized", path=request.url.path)
            return
        redis = FastAPILimiter.redis
        if redis is None:
            return

        user = await self._resolve_user(request)
        role = _effective_role(user)
        limit, window = self._limit_for_profile(role, profile)

        bucket_prefix = profile.name if profile else "role"
        bucket_key = f"ratelimit:{bucket_prefix}:{build_rate_key(request, user)}"
        allowed, remaining, reset_in = await self._consume(redis, bucket_key, limit, window)
        if allowed:
            return

        route_template = _route_template(request)
        role_label = _role_label(user, role)
        logger.warning(
            "rate_limit_exceeded",
            route_template=route_template,
            key=bucket_key,
            remaining=remaining,
            reset_in_s=reset_in,
        )
        record_http_429(route_template, role_label)
        reset_epoch = int(time.time()) + max(reset_in, 0)
        headers = {
            "Retry-After": str(max(reset_in, 0)),
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(reset_epoch),
        }
        raise HTTPException(status_code=429, detail="Too Many Requests", headers=headers)

    def _limit_for_profile(self, role: Role, profile: RateLimitProfile | None) -> tuple[int, int]:
        if profile is not None:
            return max(int(profile.limit), 1), max(int(profile.window), 1)
        limits = self._role_limits.get(role)
        if limits is None:
            limits = self._role_limits[Role.viewer]
        return limits

    async def _resolve_user(self, request: Request) -> UserCtx | None:
        user = getattr(request.state, "user", None)
        if isinstance(user, UserCtx):
            return user
        auth_header = request.headers.get("authorization") or ""
        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() == "bearer" and token:
            try:
                user = await oidc.validate_access_token(token.strip(), cfg=self._cfg)
                request.state.user = user
                return user
            except oidc.OIDCValidationError:
                logger.debug("rate_limit_token_invalid", path=request.url.path)
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("rate_limit_token_error", error=str(exc))
        return None

    async def _consume(self, redis: Any, key: str, limit: int, window: int) -> tuple[bool, int, int]:
        count = await redis.incr(key)
        await redis.expire(key, window)
        remaining = max(0, limit - count)
        ttl = await redis.ttl(key)
        reset_in = ttl if isinstance(ttl, int) and ttl > 0 else window
        return count <= limit, remaining, reset_in


def _effective_role(user: UserCtx | None) -> Role:
    if not isinstance(user, UserCtx):
        return Role.viewer
    roles = user.role_set
    if Role.admin in roles:
        return Role.admin
    if Role.ops in roles:
        return Role.ops
    if Role.viewer in roles:
        return Role.viewer
    return Role.viewer


def _role_label(user: UserCtx | None, role: Role) -> str:
    if isinstance(user, UserCtx):
        return str(role.value)
    return "anon"


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        first = xff.split(",", 1)[0].strip()
        if first:
            return first
    xri = request.headers.get("x-real-ip")
    if xri:
        candidate = xri.strip()
        if candidate:
            return candidate
    client = request.client
    if client and getattr(client, "host", None):
        return client.host
    return "unknown"


def _tenant_label(user: UserCtx | None) -> str:
    if isinstance(user, UserCtx):
        issuer = (user.raw_claims or {}).get("iss")
        if isinstance(issuer, str) and issuer:
            realm = issuer.rstrip("/").rsplit("/", 1)[-1] or ""
            if realm:
                return realm.lower()
    return "public"


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    if route is not None:
        template = getattr(route, "path", None)
        if isinstance(template, str) and template:
            return template
    return request.url.path


def build_rate_key(request: Request, user: UserCtx | None) -> str:
    tenant = _tenant_label(user)
    role = _role_label(user, _effective_role(user))
    route_template = _route_template(request)
    subject = user.sub if isinstance(user, UserCtx) and user.sub else _client_ip(request)
    return f"{tenant}:{subject}:{role}:{route_template}"


def rate_limit_dependency(
    *, profile: RateLimitProfile | None = None, cfg: Settings | None = None
) -> Callable[[Request], Awaitable[None]]:
    limiter = SmartRateLimiter(cfg or settings)
    return limiter.dependency(profile=profile)


def score_rate_limiter(cfg: Settings | None = None) -> Callable[[Request], Awaitable[None]]:
    limiter = SmartRateLimiter(cfg or settings)
    return limiter.dependency(profile=limiter.score_profile)


def roi_by_vendor_rate_limiter(cfg: Settings | None = None) -> Callable[[Request], Awaitable[None]]:
    limiter = SmartRateLimiter(cfg or settings)
    return limiter.dependency(profile=limiter.roi_by_vendor_profile)


__all__ = [
    "RateLimitProfile",
    "SmartRateLimiter",
    "build_rate_key",
    "rate_limit_dependency",
    "roi_by_vendor_rate_limiter",
    "score_rate_limiter",
]
