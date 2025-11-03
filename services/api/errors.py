from typing import Any

import psycopg
import sentry_sdk
import structlog
from asgi_correlation_id import correlation_id
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse


def _payload(error_type: str, message: str, request: Request) -> dict[str, Any]:
    request_id = correlation_id.get() or request.headers.get("X-Request-ID")
    return {"error": {"type": error_type, "message": message, "request_id": request_id}}


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        structlog.get_logger().info("validation_error", errors=exc.errors())
        payload = _payload("validation_error", "Invalid request", request)
        payload["details"] = exc.errors()
        return JSONResponse(status_code=422, content=payload)

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        log = structlog.get_logger()
        if exc.status_code == 429:
            log.warning("rate_limited", detail=str(exc.detail))
            return JSONResponse(
                status_code=429,
                content=_payload("rate_limited", "Too Many Requests", request),
            )
        log.warning("http_error", status_code=exc.status_code, detail=str(exc.detail))
        payload = _payload("http_error", str(exc.detail), request)
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(psycopg.Error)
    async def _db_exception_handler(request: Request, exc: psycopg.Error) -> JSONResponse:
        structlog.get_logger().error("db_error", pgcode=getattr(exc, "pgcode", None))
        payload = _payload("db_unavailable", "Database temporarily unavailable", request)
        return JSONResponse(status_code=500, content=payload)

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        structlog.get_logger().exception("unhandled_error")
        sentry_sdk.capture_exception(exc)
        payload = _payload("internal_error", "Internal server error", request)
        return JSONResponse(status_code=500, content=payload)
