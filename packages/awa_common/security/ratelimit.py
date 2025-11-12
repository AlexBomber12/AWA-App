from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from functools import wraps
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from awa_common.security import oidc
from awa_common.security.models import Role, UserCtx
from awa_common.settings import parse_rate_limit, settings as default_settings

logger = logging.getLogger(__name__)

_DEFAULT_SKIP_PATHS = {"/ready", "/health", "/metrics"}


def _select_role(user: UserCtx | None) -> Role:
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


def _rate_limit_identifier(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if isinstance(user, UserCtx) and getattr(user, "sub", None):
        return f"user:{user.sub}"
    return f"ip:{_client_ip(request)}"


def _normalize_limit(value: Any, fallback: str) -> tuple[int, int]:
    if isinstance(value, tuple) and len(value) == 2:
        return int(value[0]), int(value[1])
    if isinstance(value, list | Sequence) and len(value) == 2:
        return int(value[0]), int(value[1])
    target = value if value is not None else fallback
    if not isinstance(target, str):
        raise ValueError(f"Unsupported rate limit type: {type(target)}")
    return parse_rate_limit(target)


def _resolve_limit_for_role(
    role: Role,
    overrides: Mapping[Role, Any],
    cfg: Any,
) -> tuple[int, int]:
    if role is Role.admin:
        return _normalize_limit(overrides.get(Role.admin), cfg.RATE_LIMIT_ADMIN)
    if role is Role.ops:
        return _normalize_limit(overrides.get(Role.ops), cfg.RATE_LIMIT_OPS)
    return _normalize_limit(overrides.get(Role.viewer), cfg.RATE_LIMIT_VIEWER)


def RoleBasedRateLimiter(  # noqa: C901
    viewer: Any = None,
    ops: Any = None,
    admin: Any = None,
    *,
    settings: Any | None = None,
    skip_paths: Iterable[str] | None = None,
) -> Callable[[Request], Awaitable[None]]:
    """Return a dependency enforcing rate limits based on request role."""

    cfg = settings or default_settings
    skip = {path for path in (skip_paths or [])} | _DEFAULT_SKIP_PATHS
    overrides = {Role.viewer: viewer, Role.ops: ops, Role.admin: admin}

    env = getattr(cfg, "ENV", "local") or "local"
    env = env.lower()
    prod_like = {"stage", "prod"}

    async def dependency(request: Request) -> None:  # noqa: C901
        if getattr(request.state, "skip_rate_limit", False):
            return
        if request.url.path in skip:
            return
        limiter_ready = getattr(FastAPILimiter, "redis", None) is not None
        if not limiter_ready:
            if env in prod_like:
                raise HTTPException(status_code=503, detail="Rate limiter not ready")
            logger.warning("rate_limiter_not_initialized", path=request.url.path)
            return

        user = getattr(request.state, "user", None)
        if not isinstance(user, UserCtx):
            auth_header = request.headers.get("authorization") or ""
            scheme, _, token = auth_header.partition(" ")
            if scheme.lower() == "bearer" and token:
                try:
                    user = await oidc.validate_access_token(token.strip(), cfg)
                    request.state.user = user
                except oidc.OIDCValidationError:
                    logger.debug("rate_limit_token_invalid", path=request.url.path)
                except Exception as exc:  # pragma: no cover - defensive
                    logger.debug("rate_limit_token_error", error=str(exc))
                    user = None
            else:
                user = None

        role = _select_role(user if isinstance(user, UserCtx) else None)
        times, seconds = _resolve_limit_for_role(role, overrides, cfg)

        limiter = RateLimiter(times=times, seconds=seconds, identifier=_rate_limit_identifier)
        try:
            await limiter(request)
        except TypeError as exc:
            message = str(exc)
            if "required positional argument" not in message:
                raise
            await limiter(request, None)

    return dependency


def install_role_based_rate_limit(app: FastAPI, settings: Any | None = None) -> None:
    dependency = RoleBasedRateLimiter(settings=settings or default_settings)
    app.router.dependencies.append(Depends(dependency))


def no_rate_limit(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to mark an endpoint as exempt from rate limiting."""

    def _mark_request(args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
        for value in list(kwargs.values()) + list(args):
            if isinstance(value, Request):
                value.state.skip_rate_limit = True
                return

    if asyncio.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            _mark_request(args, kwargs)
            return await func(*args, **kwargs)

        return async_wrapper

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        _mark_request(args, kwargs)
        return func(*args, **kwargs)

    return sync_wrapper


__all__ = [
    "RoleBasedRateLimiter",
    "install_role_based_rate_limit",
    "no_rate_limit",
]
