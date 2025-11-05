from __future__ import annotations

import uuid
from typing import Awaitable, Callable

import structlog
from asgi_correlation_id import correlation_id
from awa_common.security import oidc
from awa_common.security.models import Role, UserCtx
from awa_common.settings import settings
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_limiter.depends import RateLimiter
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = structlog.get_logger(__name__)
_bearer = HTTPBearer(auto_error=False)
_AUTH_HEADERS = {"WWW-Authenticate": "Bearer"}


def get_request_id(request: Request) -> str:
    """Return a request id from the header or correlation middleware."""
    existing = getattr(request.state, "request_id", None)
    if isinstance(existing, str) and existing:
        return existing
    request_id = correlation_id.get() or request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    return request_id


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Ensure request scoped metadata (request_id) is always present."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = get_request_id(request)
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
            return response
        finally:
            structlog.contextvars.unbind_contextvars("request_id")


async def current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UserCtx:
    if credentials is None or credentials.scheme.lower() != "bearer":
        logger.warning("auth_missing_credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers=_AUTH_HEADERS,
        )
    token = credentials.credentials.strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers=_AUTH_HEADERS,
        )
    try:
        user = oidc.validate_access_token(token, cfg=settings)
    except oidc.OIDCValidationError as exc:
        logger.warning("auth_token_invalid", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers=_AUTH_HEADERS,
        ) from exc
    request.state.user = user
    return user


def require_roles(*required: Role) -> Callable[..., Awaitable[UserCtx]]:
    allowed = {role for role in required if role}

    async def dependency(user: UserCtx = Depends(current_user)) -> UserCtx:
        if not allowed:
            return user
        if user.role_set & allowed:
            return user
        logger.warning("auth_forbidden", user_roles=[role.value for role in user.roles])
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )

    return dependency


require_viewer = require_roles(Role.viewer, Role.ops, Role.admin)
require_ops = require_roles(Role.ops, Role.admin)
require_admin = require_roles(Role.admin)


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        ip = xff.split(",")[0].strip()
        if ip:
            return ip
    xri = request.headers.get("x-real-ip")
    if xri:
        return xri.strip()
    client = request.client
    if client and getattr(client, "host", None):
        return client.host
    return "unknown"


def _rate_limit_identifier(request: Request) -> str:
    user: UserCtx | None = getattr(request.state, "user", None)
    if user is not None:
        return f"user:{user.sub}"
    return f"ip:{_client_ip(request)}"


def limit_viewer() -> RateLimiter:
    return RateLimiter(
        times=settings.RATE_LIMIT_VIEWER_TIMES,
        seconds=settings.RATE_LIMIT_VIEWER_SECONDS,
        identifier=_rate_limit_identifier,
    )


def limit_ops() -> RateLimiter:
    return RateLimiter(
        times=settings.RATE_LIMIT_OPS_TIMES,
        seconds=settings.RATE_LIMIT_OPS_SECONDS,
        identifier=_rate_limit_identifier,
    )


def limit_admin() -> RateLimiter:
    return RateLimiter(
        times=settings.RATE_LIMIT_ADMIN_TIMES,
        seconds=settings.RATE_LIMIT_ADMIN_SECONDS,
        identifier=_rate_limit_identifier,
    )


def install_security(app: FastAPI) -> None:
    """Attach security middleware to the FastAPI application."""
    app.add_middleware(RequestContextMiddleware)


__all__ = [
    "current_user",
    "get_request_id",
    "install_security",
    "limit_admin",
    "limit_ops",
    "limit_viewer",
    "require_admin",
    "require_ops",
    "require_roles",
    "require_viewer",
    "RequestContextMiddleware",
]
