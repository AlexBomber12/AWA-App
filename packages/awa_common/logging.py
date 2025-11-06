from __future__ import annotations

import json
import logging
import sys
import uuid
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from structlog.contextvars import bind_contextvars, clear_contextvars, unbind_contextvars
from structlog.stdlib import BoundLogger, LoggerFactory
from structlog.types import Processor

STATIC_CONTEXT: dict[str, str] = {}


def configure_logging(*, service: str, env: str, version: str, level: str = "INFO") -> None:
    """Configure structlog JSON logging with shared context."""
    level_value = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=level_value, stream=sys.stdout, format="%(message)s", force=True)

    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.JSONRenderer(serializer=_serialize_json),
    ]
    structlog.configure(
        processors=processors,
        logger_factory=LoggerFactory(),
        wrapper_class=BoundLogger,
        cache_logger_on_first_use=True,
    )

    STATIC_CONTEXT.clear()
    STATIC_CONTEXT.update({"service": service, "env": env, "version": version})
    clear_contextvars()
    bind_contextvars(**STATIC_CONTEXT)


def _serialize_json(event_dict: dict[str, object], **kwargs: Any) -> str:
    options = {"separators": (",", ":"), "sort_keys": False}
    options.update(kwargs)
    return json.dumps(event_dict, **options)


def bind_user_sub(user_sub: str | None) -> None:
    """Attach the current user sub claim to the logging context."""
    if user_sub:
        bind_contextvars(user_sub=user_sub)
    else:
        try:
            unbind_contextvars("user_sub")
        except LookupError:
            pass


def bind_request(request_id: str, trace_id: str | None = None) -> None:
    """Bind correlation identifiers into the logging context."""
    if not request_id:
        request_id = str(uuid.uuid4())
    if not trace_id:
        trace_id = request_id
    bind_contextvars(request_id=request_id, trace_id=trace_id)


def clear_context() -> None:
    """Reset request-scoped context while preserving static fields."""
    clear_contextvars()
    if STATIC_CONTEXT:
        bind_contextvars(**STATIC_CONTEXT)


def bind_celery_task() -> None:
    """Bind Celery task metadata (task_id) into the logging context if available."""
    try:
        from celery import current_task  # type: ignore
    except Exception:  # pragma: no cover - Celery optional
        return
    task = current_task
    if task is None:
        return
    request = getattr(task, "request", None)
    if request is None:
        return
    task_id = getattr(request, "id", None) or getattr(request, "task_id", None)
    if task_id:
        bind_contextvars(task_id=task_id)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Ensure every request has correlation ids and propagate them."""

    header_name = "X-Request-ID"

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(self.header_name) or str(uuid.uuid4())
        traceparent = request.headers.get("traceparent")
        trace_id = _extract_trace_id(traceparent) or request.headers.get("X-Trace-ID") or request_id

        request.state.request_id = request_id
        request.state.trace_id = trace_id

        bind_request(request_id, trace_id)
        response: Response | None = None

        try:
            response = await call_next(request)
            return response
        finally:
            if response is not None:
                response.headers.setdefault(self.header_name, request_id)
                if trace_id:
                    response.headers.setdefault("X-Trace-ID", trace_id)
            clear_context()


def _extract_trace_id(traceparent: str | None) -> str | None:
    if not traceparent:
        return None
    parts = traceparent.split("-")
    if len(parts) >= 2:
        candidate = parts[1].strip()
        if len(candidate) == 32:
            return candidate
    return None


__all__ = [
    "RequestIdMiddleware",
    "bind_request",
    "bind_user_sub",
    "clear_context",
    "configure_logging",
    "bind_celery_task",
]
