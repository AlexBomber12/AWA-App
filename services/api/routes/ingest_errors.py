from __future__ import annotations

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse

from awa_common.metrics import record_api_ingest_4xx_total, record_api_ingest_5xx_total
from services.api.schemas import ErrorCode, ErrorResponse
from services.api.security import get_request_id

logger = structlog.get_logger(__name__)


class IngestRequestError(Exception):
    """Raised when an ingest or upload request cannot be processed."""

    def __init__(self, *, status_code: int, code: ErrorCode, detail: str, hint: str | None = None) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.detail = detail
        self.hint = hint


def _log_ingest_error(
    *,
    request: Request,
    route: str,
    status_code: int,
    code: ErrorCode,
    detail: str,
) -> None:
    user_sub = getattr(getattr(request.state, "user", None), "sub", None)
    request_id = get_request_id(request)
    bound = logger.bind(route=route, request_id=request_id, user_sub=user_sub)
    log = bound.warning if status_code < 500 else bound.error
    log(
        "ingest_error",
        error_code=code,
        error_detail=detail,
        status_code=status_code,
    )


def ingest_error_response(
    request: Request,
    *,
    status_code: int,
    code: ErrorCode,
    detail: str,
    hint: str | None = None,
    route: str,
) -> JSONResponse:
    """Render a structured error response for ingest-style endpoints."""

    request_id = get_request_id(request)
    payload = ErrorResponse(code=code, detail=detail, hint=hint, request_id=request_id)
    response = JSONResponse(status_code=status_code, content=payload.model_dump())
    response.headers.setdefault("X-Request-ID", request_id)
    _log_ingest_error(request=request, route=route, status_code=status_code, code=code, detail=detail)
    if 400 <= status_code < 500:
        record_api_ingest_4xx_total(code)
    else:
        record_api_ingest_5xx_total()
    return response


def respond_with_ingest_error(request: Request, exc: IngestRequestError, *, route: str) -> JSONResponse:
    return ingest_error_response(
        request,
        status_code=exc.status_code,
        code=exc.code,
        detail=exc.detail,
        hint=exc.hint,
        route=route,
    )


__all__ = ["IngestRequestError", "ingest_error_response", "respond_with_ingest_error"]
