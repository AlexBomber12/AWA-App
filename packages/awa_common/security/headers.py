from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class _SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, *, settings: Any) -> None:
        super().__init__(app)
        self._settings = settings

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        response: Response = await call_next(request)

        def _set_if_missing(header: str, value: str | None) -> None:
            if not value:
                return
            if header in response.headers:
                return  # Respect explicit header set by route.
            response.headers[header] = value

        _set_if_missing("X-Content-Type-Options", self._settings.SECURITY_X_CONTENT_TYPE_OPTIONS)
        _set_if_missing("X-Frame-Options", self._settings.SECURITY_FRAME_OPTIONS)
        _set_if_missing("Referrer-Policy", self._settings.SECURITY_REFERRER_POLICY)
        if getattr(self._settings, "SECURITY_HSTS_ENABLED", False):
            env = getattr(self._settings, "ENV", "local")
            if env in {"stage", "prod"}:
                _set_if_missing(
                    "Strict-Transport-Security",
                    "max-age=31536000; includeSubDomains; preload",
                )

        return response


def install_security_headers(app: FastAPI, settings: Any) -> None:
    """Install middleware that enforces security headers on responses."""
    app.add_middleware(_SecurityHeadersMiddleware, settings=settings)


__all__ = ["install_security_headers"]
