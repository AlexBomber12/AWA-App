from __future__ import annotations

import os
import threading
import time
from collections.abc import Callable, Iterable
from contextlib import contextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    start_http_server,
)
from starlette.middleware.base import BaseHTTPMiddleware

from awa_common.logging import bind_celery_task

try:  # pragma: no cover - optional runtime dependency
    from prometheus_client.multiprocess import MultiProcessCollector
except Exception:  # pragma: no cover - multiprocess optional in tests
    MultiProcessCollector = None  # type: ignore

BASE_LABELS = ("service", "env", "version")
HTTP_BUCKETS = (0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10)


def _create_registry() -> CollectorRegistry:
    registry = CollectorRegistry()
    multiproc_dir = os.getenv("PROMETHEUS_MULTIPROC_DIR")
    if multiproc_dir and MultiProcessCollector is not None:
        MultiProcessCollector(registry)
    return registry


REGISTRY: CollectorRegistry = _create_registry()


def _default_labels(service: str | None, env: str | None, version: str | None) -> dict[str, str]:
    resolved_service = (service or os.getenv("SERVICE_NAME") or "").strip()
    if not resolved_service:
        resolved_service = "api"
    resolved_env = (env or os.getenv("APP_ENV") or os.getenv("ENV") or "").strip() or "local"
    resolved_version = (
        version or os.getenv("APP_VERSION") or os.getenv("RELEASE") or ""
    ).strip() or "0.0.0"
    return {
        "service": resolved_service,
        "env": resolved_env,
        "version": resolved_version,
    }


_BASE_LABEL_VALUES: dict[str, str] = _default_labels(None, None, None)


def init(*, service: str | None = None, env: str | None = None, version: str | None = None) -> None:
    """Set common label defaults for metrics."""
    global _BASE_LABEL_VALUES
    _BASE_LABEL_VALUES = _default_labels(service, env, version)


def _with_base_labels(**labels: str) -> dict[str, str]:
    merged = dict(_BASE_LABEL_VALUES)
    merged.update(labels)
    return merged


HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "HTTP request count",
    ("method", "path_template", "status", *BASE_LABELS),
    registry=REGISTRY,
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ("method", "path_template", "status", *BASE_LABELS),
    buckets=HTTP_BUCKETS,
    registry=REGISTRY,
)

TASK_RUNS_TOTAL = Counter(
    "task_runs_total",
    "Celery task executions by outcome",
    ("task_name", "outcome", *BASE_LABELS),
    registry=REGISTRY,
)
TASK_DURATION_SECONDS = Histogram(
    "task_duration_seconds",
    "Celery task execution duration",
    ("task_name", *BASE_LABELS),
    buckets=HTTP_BUCKETS,
    registry=REGISTRY,
)
TASK_FAILURES_TOTAL = Counter(
    "task_failures_total",
    "Celery task failures by exception",
    ("task_name", "exc_type", *BASE_LABELS),
    registry=REGISTRY,
)

ETL_RUNS_TOTAL = Counter(
    "etl_runs_total",
    "ETL pipeline executions by status",
    ("source", "status", *BASE_LABELS),
    registry=REGISTRY,
)
ETL_FAILURES_TOTAL = Counter(
    "etl_failures_total",
    "ETL pipeline failures by reason",
    ("source", "reason", *BASE_LABELS),
    registry=REGISTRY,
)
ETL_RETRY_TOTAL = Counter(
    "etl_retry_total",
    "Retry attempts during ETL HTTP calls",
    ("source", "code", *BASE_LABELS),
    registry=REGISTRY,
)
ETL_DURATION_SECONDS = Histogram(
    "etl_duration_seconds",
    "ETL pipeline duration in seconds",
    ("source", *BASE_LABELS),
    buckets=HTTP_BUCKETS,
    registry=REGISTRY,
)

QUEUE_BACKLOG = Gauge(
    "queue_backlog",
    "Celery queue backlog",
    ("queue", *BASE_LABELS),
    registry=REGISTRY,
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record Prometheus metrics for FastAPI HTTP requests."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        start = time.perf_counter()
        method = request.method.upper()
        status_code = 500
        path_template = _path_template(request)
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except HTTPException as exc:
            status_code = exc.status_code
            raise
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.perf_counter() - start
            labels = _with_base_labels(
                method=method,
                path_template=path_template,
                status=str(status_code),
            )
            HTTP_REQUESTS_TOTAL.labels(**labels).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(**labels).observe(duration)


def _path_template(request: Request) -> str:
    route = request.scope.get("route")
    if route is None:
        return request.url.path
    candidate = getattr(route, "path", None)
    if isinstance(candidate, str) and candidate:
        return candidate
    path_format = getattr(route, "path_format", None)
    if isinstance(path_format, str) and path_format:
        return path_format
    formatter = getattr(route, "path_format", None)
    if formatter is not None:
        maybe_callable = getattr(formatter, "__str__", None)
        if callable(maybe_callable):
            text = maybe_callable()
            if isinstance(text, str) and text:
                return text
    return request.url.path


def register_metrics_endpoint(app: FastAPI) -> None:
    """Expose `/metrics` endpoint using the shared registry."""

    @app.get("/metrics", include_in_schema=False)
    async def _metrics() -> Response:
        payload = generate_latest(REGISTRY)
        return Response(content=payload, media_type=CONTENT_TYPE_LATEST)


_TASK_START: dict[str, tuple[str, float]] = {}
_TASK_LOCK = threading.Lock()
_CELERY_METRICS_ENABLED = False
_BACKLOG_THREAD: threading.Thread | None = None
_BACKLOG_LOCK = threading.Lock()


def _task_label(sender: Any) -> str:
    name = getattr(sender, "name", None)
    if isinstance(name, str) and name:
        return name
    if isinstance(sender, str):
        return sender
    cls = getattr(sender, "__class__", None)
    cls_name = getattr(cls, "__name__", None)
    if isinstance(cls_name, str) and cls_name:
        return cls_name
    return "unknown"


def enable_celery_metrics(
    celery_app: Any,
    *,
    broker_url: str | None,
    queue_names: Iterable[str] | None = None,
    backlog_interval_s: int = 15,
) -> None:
    """Register Celery signal handlers and optional backlog polling."""
    global _CELERY_METRICS_ENABLED
    if _CELERY_METRICS_ENABLED:
        return

    try:
        from celery import signals  # type: ignore
    except Exception:  # pragma: no cover - Celery not installed in some environments
        return

    signals.task_prerun.connect(on_task_prerun, weak=False)
    signals.task_postrun.connect(on_task_postrun, weak=False)
    signals.task_failure.connect(on_task_failure, weak=False)

    _maybe_start_backlog_probe(
        broker_url=broker_url, queue_names=queue_names, interval=backlog_interval_s
    )
    _CELERY_METRICS_ENABLED = True


def on_task_prerun(sender: Any, task_id: str, **_kwargs: Any) -> None:
    """Celery signal handler for task_prerun."""
    task_name = _task_label(sender)
    TASK_RUNS_TOTAL.labels(**_with_base_labels(task_name=task_name, outcome="start")).inc()
    bind_celery_task()
    if not task_id:
        return
    with _TASK_LOCK:
        _TASK_START[task_id] = (task_name, time.perf_counter())


def on_task_postrun(sender: Any, task_id: str, **kwargs: Any) -> None:
    """Celery signal handler for task_postrun."""
    task_name = _task_label(sender)
    state = kwargs.get("state") or "unknown"
    outcome = str(state).lower()
    TASK_RUNS_TOTAL.labels(**_with_base_labels(task_name=task_name, outcome=outcome)).inc()
    start_time = None
    if task_id:
        with _TASK_LOCK:
            start_time = _TASK_START.pop(task_id, None)
    if start_time is not None:
        _, started_at = start_time
        duration = time.perf_counter() - started_at
        TASK_DURATION_SECONDS.labels(**_with_base_labels(task_name=task_name)).observe(duration)


def on_task_failure(
    sender: Any, task_id: str, exception: BaseException | None = None, **_kwargs: Any
) -> None:
    """Celery signal handler for task_failure."""
    task_name = _task_label(sender)
    exc_name = "unknown"
    if exception is not None:
        exc_name = exception.__class__.__name__
    TASK_FAILURES_TOTAL.labels(**_with_base_labels(task_name=task_name, exc_type=exc_name)).inc()


def _maybe_start_backlog_probe(
    *,
    broker_url: str | None,
    queue_names: Iterable[str] | None,
    interval: int,
) -> None:
    global _BACKLOG_THREAD
    if _BACKLOG_THREAD is not None:
        return
    if not broker_url or not queue_names:
        return
    lower = broker_url.lower()
    if not (lower.startswith("redis://") or lower.startswith("rediss://")):
        return

    try:
        import redis  # type: ignore
    except Exception:  # pragma: no cover - redis dependency optional
        return

    queues = tuple(q for q in queue_names if q)
    if not queues:
        return

    def _probe() -> None:
        try:
            client = redis.Redis.from_url(broker_url, decode_responses=False)
        except Exception:
            return
        while True:
            for queue in queues:
                try:
                    backlog = client.llen(queue)
                except Exception:
                    continue
                QUEUE_BACKLOG.labels(**_with_base_labels(queue=queue)).set(float(backlog))
            time.sleep(max(interval, 1))

    with _BACKLOG_LOCK:
        if _BACKLOG_THREAD is None:
            thread = threading.Thread(target=_probe, name="queue-backlog-metrics", daemon=True)
            _BACKLOG_THREAD = thread
            thread.start()


@contextmanager
def record_etl_run(source: str):
    """Record metrics for ETL pipelines."""
    start_time = time.perf_counter()
    base_labels = _with_base_labels(source=source)
    try:
        yield
    except Exception as exc:
        duration = time.perf_counter() - start_time
        failure_labels = {**base_labels, "reason": exc.__class__.__name__}
        ETL_FAILURES_TOTAL.labels(**failure_labels).inc()
        ETL_RUNS_TOTAL.labels(**{**base_labels, "status": "failed"}).inc()
        ETL_DURATION_SECONDS.labels(**base_labels).observe(duration)
        raise
    else:
        duration = time.perf_counter() - start_time
        ETL_RUNS_TOTAL.labels(**{**base_labels, "status": "success"}).inc()
        ETL_DURATION_SECONDS.labels(**base_labels).observe(duration)


def record_etl_skip(source: str) -> None:
    """Increment skip counter for ETL runs that were deduplicated."""
    ETL_RUNS_TOTAL.labels(**{**_with_base_labels(source=source), "status": "skipped"}).inc()


def record_etl_retry(source: str, code: int | str) -> None:
    """Increment retry counter for ETL HTTP attempts."""
    ETL_RETRY_TOTAL.labels(**{**_with_base_labels(source=source), "code": str(code)}).inc()


def start_worker_metrics_http_if_enabled(port_env: str = "WORKER_METRICS_PORT") -> None:
    """Start HTTP exporter for worker metrics if enabled via env."""
    if os.getenv("WORKER_METRICS_HTTP", "0") not in {"1", "true", "TRUE"}:
        return
    port_value = os.getenv(port_env, "9108")
    try:
        port = int(port_value)
    except ValueError:
        port = 9108
    start_http_server(port, registry=REGISTRY)


__all__ = [
    "CONTENT_TYPE_LATEST",
    "HTTP_REQUESTS_TOTAL",
    "HTTP_REQUEST_DURATION_SECONDS",
    "TASK_RUNS_TOTAL",
    "TASK_DURATION_SECONDS",
    "TASK_FAILURES_TOTAL",
    "ETL_RUNS_TOTAL",
    "ETL_FAILURES_TOTAL",
    "ETL_RETRY_TOTAL",
    "ETL_DURATION_SECONDS",
    "QUEUE_BACKLOG",
    "MetricsMiddleware",
    "REGISTRY",
    "enable_celery_metrics",
    "init",
    "on_task_failure",
    "on_task_postrun",
    "on_task_prerun",
    "record_etl_run",
    "record_etl_skip",
    "record_etl_retry",
    "register_metrics_endpoint",
    "start_worker_metrics_http_if_enabled",
]
