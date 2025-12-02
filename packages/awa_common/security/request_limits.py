from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class _RequestTooLarge(Exception):
    """Raised when an incoming request exceeds the configured byte cap."""


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, *, settings: Any) -> None:
        super().__init__(app)
        self._settings = settings
        try:
            settings.__dict__.pop("ingestion", None)
        except Exception:
            pass
        ingest_cfg = getattr(settings, "ingestion", None)
        default_limit = getattr(settings, "MAX_REQUEST_BYTES", 1_048_576)
        self._max_bytes = int(getattr(ingest_cfg, "max_request_bytes", default_limit))

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:  # noqa: C901
        limit = self._max_bytes
        header_value = request.headers.get("content-length")
        size_hint: int | None = None
        if header_value:
            try:
                size_hint = int(header_value)
            except ValueError:
                size_hint = None
            else:
                if size_hint > limit:
                    return JSONResponse(status_code=413, content={"detail": "Request body too large"})
        original_receive = request._receive  # type: ignore[attr-defined]

        if size_hint is not None:
            request._receive = original_receive  # type: ignore[attr-defined]
            return await call_next(request)

        total = 0

        async def limited_receive() -> dict[str, Any]:
            nonlocal total
            message = await original_receive()
            if message["type"] == "http.request":
                body = message.get("body", b"") or b""
                total += len(body)
                if total > limit:
                    raise _RequestTooLarge
            return message

        request._receive = limited_receive  # type: ignore[attr-defined]
        try:
            response = await call_next(request)
        except _RequestTooLarge:
            return JSONResponse(status_code=413, content={"detail": "Request body too large"})
        except BaseExceptionGroup as exc:  # pragma: no cover - Python 3.11+ task groups
            for err in exc.exceptions:
                if isinstance(err, _RequestTooLarge):
                    return JSONResponse(status_code=413, content={"detail": "Request body too large"})
            raise
        finally:
            request._receive = original_receive  # type: ignore[attr-defined]

        return response


def install_body_size_limit(app: FastAPI, settings: Any) -> None:
    app.add_middleware(BodySizeLimitMiddleware, settings=settings)


__all__ = ["BodySizeLimitMiddleware", "install_body_size_limit"]
