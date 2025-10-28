from __future__ import annotations

import logging
import time
from typing import Any, Awaitable, Callable, Mapping

from asgi_correlation_id import correlation_id
from awa_common.settings import settings
from fastapi import Request, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from services.api.security import Principal

logger = logging.getLogger(__name__)

_AUDIT_COLUMNS = (
    "user_id",
    "email",
    "roles",
    "method",
    "path",
    "route",
    "status",
    "latency_ms",
    "ip",
    "ua",
    "request_id",
)

_AUDIT_INSERT = text(
    """
    INSERT INTO audit_log (
        user_id, email, roles, method, path, route,
        status, latency_ms, ip, ua, request_id
    )
    VALUES (
        :user_id, :email, :roles, :method, :path, :route,
        :status, :latency_ms, :ip, :ua, :request_id
    )
    """
)


def _extract_ip(request: Request) -> str:
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


async def insert_audit(session: AsyncSession, record: Mapping[str, Any]) -> None:
    payload = {column: record.get(column) for column in _AUDIT_COLUMNS}
    await session.execute(_AUDIT_INSERT, payload)


class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(
        self, app: ASGIApp, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        super().__init__(app)
        self._session_factory = session_factory

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = int((time.perf_counter() - start) * 1000)

        path = request.url.path
        should_persist = (
            settings.AUTH_MODE != "disabled" and settings.should_protect_path(path)
        )
        principal: Principal | None = getattr(request.state, "principal", None)
        if not should_persist and principal is None:
            return response

        route = request.scope.get("route")
        if route is not None:
            route_pattern = getattr(route, "path_format", None) or getattr(
                route, "path", None
            )
        else:
            route_pattern = None

        record = {
            "user_id": principal.id if principal else None,
            "email": principal.email if principal else None,
            "roles": sorted(principal.roles) if principal else None,
            "method": request.method,
            "path": path,
            "route": route_pattern or path,
            "status": getattr(response, "status_code", None),
            "latency_ms": latency_ms,
            "ip": _extract_ip(request),
            "ua": request.headers.get("user-agent"),
            "request_id": correlation_id.get() or request.headers.get("X-Request-ID"),
        }

        try:
            async with self._session_factory() as session:
                await insert_audit(session, record)
                await session.commit()
        except Exception:
            logger.warning("audit_log_write_failed", exc_info=True)
        return response
