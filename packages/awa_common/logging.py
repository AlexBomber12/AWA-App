from __future__ import annotations

import json
import logging
import sys
import uuid
from collections.abc import Callable
from contextvars import ContextVar
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from structlog import contextvars as structlog_contextvars
from structlog.stdlib import BoundLogger, LoggerFactory, ProcessorFormatter

from awa_common.settings import settings

STATIC_CONTEXT: dict[str, str] = {}
_REQUEST_ID: ContextVar[str | None] = ContextVar("request_id", default=None)
_TRACE_ID: ContextVar[str | None] = ContextVar("trace_id", default=None)


def configure_logging(service: str, level: str | None = None) -> None:
    """Configure structlog JSON logging with shared/static context."""

    env = getattr(settings, "ENV", "local")
    version = getattr(settings, "VERSION", None) or getattr(settings, "APP_VERSION", None) or "0.0.0"
    configured_level = (level or getattr(settings, "LOG_LEVEL", "INFO")).upper()
    level_value = getattr(logging, configured_level, logging.INFO)

    STATIC_CONTEXT.clear()
    STATIC_CONTEXT.update(
        {
            "service": service,
            "env": env,
            "version": version,
        }
    )

    structlog_contextvars.clear_contextvars()
    structlog_contextvars.bind_contextvars(**STATIC_CONTEXT)
    _REQUEST_ID.set(None)
    _TRACE_ID.set(None)

    json_renderer = structlog.processors.JSONRenderer(serializer=_serialize_json)
    shared_processors: list[Callable[..., Any]] = [
        structlog_contextvars.merge_contextvars,
        _inject_static_context,
        _ensure_request_fields,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True, key="ts"),
        structlog.processors.EventRenamer("msg"),
        _ensure_optional_fields,
    ]

    formatter = ProcessorFormatter(
        processor=json_renderer,
        foreign_pre_chain=shared_processors,
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logging.basicConfig(handlers=[handler], level=level_value, force=True)

    structlog.configure(
        processors=[*shared_processors, ProcessorFormatter.wrap_for_formatter],
        wrapper_class=BoundLogger,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _serialize_json(event_dict: dict[str, Any], **kwargs: Any) -> str:
    options = {"separators": (",", ":"), "sort_keys": False}
    options.update(kwargs)
    return json.dumps(event_dict, **options)


def _inject_static_context(_logger: BoundLogger, _name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    for key, value in STATIC_CONTEXT.items():
        event_dict.setdefault(key, value)
    return event_dict


def _ensure_request_fields(_logger: BoundLogger, _name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    request_id = event_dict.get("request_id")
    if request_id is None:
        request_id = _REQUEST_ID.get()
    trace_id = event_dict.get("trace_id")
    if trace_id is None:
        trace_id = _TRACE_ID.get() or request_id
    event_dict["request_id"] = request_id
    event_dict["trace_id"] = trace_id
    return event_dict


def _ensure_optional_fields(_logger: BoundLogger, _name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    event_dict.setdefault("component", None)
    event_dict.setdefault("task", None)
    return event_dict


def bind_user_sub(user_sub: str | None) -> None:
    """Attach the current user sub claim to the logging context."""
    if user_sub:
        structlog_contextvars.bind_contextvars(user_sub=user_sub)
        return
    try:
        structlog_contextvars.unbind_contextvars("user_sub")
    except LookupError:
        pass


def set_request_context(request_id: str | None, trace_id: str | None = None) -> tuple[str, str]:
    """Bind correlation identifiers into the logging context."""
    request_id = request_id or str(uuid.uuid4())
    trace_id = trace_id or request_id
    _REQUEST_ID.set(request_id)
    _TRACE_ID.set(trace_id)
    structlog_contextvars.bind_contextvars(request_id=request_id, trace_id=trace_id)
    return request_id, trace_id


def clear_request_context() -> None:
    """Reset request-scoped context while preserving static fields."""
    _REQUEST_ID.set(None)
    _TRACE_ID.set(None)
    structlog_contextvars.clear_contextvars()
    if STATIC_CONTEXT:
        structlog_contextvars.bind_contextvars(**STATIC_CONTEXT)


def bind_celery_task(task_name: str | None = None, *, task_id: str | None = None) -> None:
    """Bind Celery task metadata into the logging context if available."""
    if task_name is None or task_id is None:
        try:
            from celery import current_task  # type: ignore
        except Exception:  # pragma: no cover - optional dependency
            return
        task = current_task
        if task is None:
            return
        request = getattr(task, "request", None)
        if request is None:
            return
        if task_name is None:
            inferred = getattr(request, "task", None) or getattr(task, "name", None)
            task_name = inferred or getattr(task, "__class__", type(task)).__name__
        if task_id is None:
            task_id = getattr(request, "id", None) or getattr(request, "task_id", None)
    updates: dict[str, Any] = {}
    if task_name:
        updates["task"] = task_name
    if task_id:
        updates["task_id"] = task_id
        if not _REQUEST_ID.get():
            set_request_context(task_id, task_id)
    if updates:
        structlog_contextvars.bind_contextvars(**updates)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Ensure every request has correlation ids and propagate them."""

    header_name = "X-Request-ID"

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
        request_id = request.headers.get(self.header_name) or str(uuid.uuid4())
        traceparent = request.headers.get("traceparent")
        trace_id = _extract_trace_id(traceparent) or request.headers.get("X-Trace-ID") or request_id

        request.state.request_id = request_id
        request.state.trace_id = trace_id
        set_request_context(request_id, trace_id)

        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            if response is not None:
                response.headers.setdefault(self.header_name, request_id)
                if trace_id:
                    response.headers.setdefault("X-Trace-ID", trace_id)
            clear_request_context()


def _extract_trace_id(traceparent: str | None) -> str | None:
    if not traceparent:
        return None
    parts = traceparent.split("-")
    if len(parts) >= 2:
        candidate = parts[1].strip()
        if len(candidate) == 32:
            return candidate
    return None


def bind_request(request_id: str, trace_id: str | None = None) -> tuple[str, str]:  # pragma: no cover - legacy shim
    return set_request_context(request_id, trace_id)


def clear_context() -> None:  # pragma: no cover - legacy shim
    clear_request_context()


__all__ = [
    "RequestIdMiddleware",
    "bind_celery_task",
    "bind_request",
    "bind_user_sub",
    "clear_context",
    "clear_request_context",
    "configure_logging",
    "set_request_context",
]
