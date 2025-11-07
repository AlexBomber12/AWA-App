from __future__ import annotations

import time
from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import Request, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from awa_common.security.models import UserCtx
from awa_common.settings import settings
from services.api.security import get_request_id

logger = structlog.get_logger(__name__)

_EXCLUDED_PATHS = {"/health", "/ready", "/metrics"}
_AUDIT_SQL = text(
    """
    INSERT INTO audit_log (
        ts, user_id, email, roles, method, path, route,
        status, latency_ms, ip, ua, request_id
    ) VALUES (
        :ts, :user_id, :email, :roles, :method, :path, :route,
        :status, :latency_ms, :ip, :ua, :request_id
    )
    """
)


async def insert_audit(session: AsyncSession, record: Mapping[str, Any]) -> None:
    filtered = dict(record)
    await session.execute(_AUDIT_SQL, filtered)


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


class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, session_factory: async_sessionmaker[AsyncSession]) -> None:
        super().__init__(app)
        self._session_factory = session_factory

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)

        if not settings.SECURITY_ENABLE_AUDIT:
            return response

        user = getattr(request.state, "user", None)
        if not isinstance(user, UserCtx):
            return response

        path = request.url.path
        if path in _EXCLUDED_PATHS:
            return response

        route = request.scope.get("route")
        route_pattern = getattr(route, "path_format", None) or getattr(route, "path", None)

        request_id = get_request_id(request)
        roles_csv = ",".join(role.value for role in user.roles)
        roles_array = "{" + roles_csv + "}" if roles_csv else None

        record = {
            "ts": datetime.now(UTC),
            "user_id": user.sub,
            "email": user.email,
            "roles": roles_array,
            "method": request.method,
            "path": path,
            "route": route_pattern or path,
            "status": getattr(response, "status_code", None),
            "latency_ms": int((time.perf_counter() - start) * 1000),
            "ip": _client_ip(request),
            "ua": request.headers.get("user-agent"),
            "request_id": request_id,
        }

        try:
            async with self._session_factory() as session:
                await insert_audit(session, record)
                await session.commit()
        except Exception:
            logger.warning(
                "audit_log_write_failed",
                request_id=request_id,
                path=path,
                user_id=user.sub,
                exc_info=True,
            )
        return response
