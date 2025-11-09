from __future__ import annotations

import asyncio
import functools
import logging
import os
import threading
import time
from collections.abc import Awaitable, Callable, Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, TypeVar, cast

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
from awa_common.settings import settings

F = TypeVar("F", bound=Callable[..., Any])

BASE_LABELS = ("service", "env", "version")
HTTP_BUCKETS = (0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10)


def _create_registry() -> CollectorRegistry:
    registry = CollectorRegistry()
    multiproc_dir = os.getenv("PROMETHEUS_MULTIPROC_DIR")
    if multiproc_dir:
        collector = _load_multiprocess_collector()
        if collector is not None:
            collector(registry)
    return registry


def _load_multiprocess_collector() -> Callable[[CollectorRegistry], None] | None:
    """Best-effort loader for the Prometheus multiprocess collector."""
    try:  # pragma: no cover - optional dependency branch
        from prometheus_client.multiprocess import MultiProcessCollector
    except Exception:  # pragma: no cover - optional dependency branch
        return None
    return cast(Callable[[CollectorRegistry], None], MultiProcessCollector)


REGISTRY: CollectorRegistry = _create_registry()
logger = logging.getLogger(__name__)
_SERVICE_NAME = "api"
_TEXTFILE_EXPORTER: _TextfileExporter | None = None
_TEXTFILE_LOCK = threading.Lock()


def _default_labels(service: str | None, env: str | None, version: str | None) -> dict[str, str]:
    resolved_service = (service or getattr(settings, "SERVICE_NAME", "") or os.getenv("SERVICE_NAME") or "").strip()
    if not resolved_service:
        resolved_service = "api"
    resolved_env = env or getattr(settings, "APP_ENV", None) or os.getenv("APP_ENV") or os.getenv("ENV") or ""
    resolved_env = (resolved_env or "").strip() or "local"
    resolved_version = (
        version
        or getattr(settings, "VERSION", None)
        or os.getenv("APP_VERSION")
        or os.getenv("RELEASE")
        or os.getenv("GIT_SHA")
        or ""
    )
    resolved_version = (resolved_version or "").strip() or "0.0.0"
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
    global _SERVICE_NAME
    _SERVICE_NAME = _BASE_LABEL_VALUES["service"]
    _maybe_start_textfile_exporter()


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
    ("task", "status", *BASE_LABELS),
    registry=REGISTRY,
)
TASK_DURATION_SECONDS = Histogram(
    "task_duration_seconds",
    "Celery task execution duration",
    ("task", *BASE_LABELS),
    buckets=HTTP_BUCKETS,
    registry=REGISTRY,
)
TASK_ERRORS_TOTAL = Counter(
    "task_errors_total",
    "Celery task failures by exception",
    ("task", "error_type", *BASE_LABELS),
    registry=REGISTRY,
)

ETL_RUNS_TOTAL = Counter(
    "etl_runs_total",
    "ETL pipeline executions by status",
    ("job", *BASE_LABELS),
    registry=REGISTRY,
)
ETL_PROCESSED_RECORDS_TOTAL = Counter(
    "etl_processed_records_total",
    "Records processed per ETL batch",
    ("job", *BASE_LABELS),
    registry=REGISTRY,
)
ETL_RETRY_TOTAL = Counter(
    "etl_retry_total",
    "Retry attempts during ETL HTTP calls",
    ("job", "reason", *BASE_LABELS),
    registry=REGISTRY,
)
ETL_DURATION_SECONDS = Histogram(
    "etl_duration_seconds",
    "ETL pipeline duration in seconds",
    ("job", *BASE_LABELS),
    buckets=HTTP_BUCKETS,
    registry=REGISTRY,
)

HTTP_CLIENT_REQUESTS_TOTAL = Counter(
    "http_client_requests_total",
    "Outbound HTTP requests",
    ("target", "method", "status_class", *BASE_LABELS),
    registry=REGISTRY,
)
HTTP_CLIENT_REQUEST_DURATION_SECONDS = Histogram(
    "http_client_request_duration_seconds",
    "Outbound HTTP request latency in seconds",
    ("target", "method", *BASE_LABELS),
    buckets=HTTP_BUCKETS,
    registry=REGISTRY,
)

QUEUE_BACKLOG = Gauge(
    "queue_backlog",
    "Celery queue backlog",
    ("queue", *BASE_LABELS),
    registry=REGISTRY,
)

ALERTS_NOTIFICATIONS_SENT_TOTAL = Counter(
    "alerts_notifications_sent_total",
    "Alert notifications delivered successfully",
    ("rule", "channel", *BASE_LABELS),
    registry=REGISTRY,
)
ALERTS_NOTIFICATIONS_FAILED_TOTAL = Counter(
    "alerts_notifications_failed_total",
    "Alert notification attempts that failed",
    ("rule", "channel", "error_type", *BASE_LABELS),
    registry=REGISTRY,
)
ALERTS_RULE_EVALUATIONS_TOTAL = Counter(
    "alerts_rule_evaluations_total",
    "Alert rule evaluation outcomes",
    ("rule", "result", *BASE_LABELS),
    registry=REGISTRY,
)
ALERTS_RULE_DURATION_SECONDS = Histogram(
    "alerts_rule_duration_seconds",
    "Alert rule evaluation duration in seconds",
    ("rule", *BASE_LABELS),
    buckets=HTTP_BUCKETS,
    registry=REGISTRY,
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record Prometheus metrics for FastAPI HTTP requests."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
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
    _celery_app: Any,
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
        from celery import signals
    except Exception:  # pragma: no cover - Celery not installed in some environments
        return

    signals.task_prerun.connect(on_task_prerun, weak=False)
    signals.task_postrun.connect(on_task_postrun, weak=False)
    signals.task_failure.connect(on_task_failure, weak=False)

    _maybe_start_backlog_probe(broker_url=broker_url, queue_names=queue_names, interval=backlog_interval_s)
    _CELERY_METRICS_ENABLED = True


def on_task_prerun(sender: Any, task_id: str, **_kwargs: Any) -> None:
    """Celery signal handler for task_prerun."""
    task_name = _task_label(sender)
    TASK_RUNS_TOTAL.labels(**_with_base_labels(task=task_name, status="start")).inc()
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
    TASK_RUNS_TOTAL.labels(**_with_base_labels(task=task_name, status=outcome)).inc()
    start_time = None
    if task_id:
        with _TASK_LOCK:
            start_time = _TASK_START.pop(task_id, None)
    if start_time is not None:
        _, started_at = start_time
        duration = time.perf_counter() - started_at
        TASK_DURATION_SECONDS.labels(**_with_base_labels(task=task_name)).observe(duration)


def on_task_failure(sender: Any, task_id: str, exception: BaseException | None = None, **_kwargs: Any) -> None:
    """Celery signal handler for task_failure."""
    task_name = _task_label(sender)
    exc_name = "unknown"
    if exception is not None:
        exc_name = exception.__class__.__name__
    TASK_ERRORS_TOTAL.labels(**_with_base_labels(task=task_name, error_type=exc_name)).inc()
    if task_id:
        logger.debug("celery_task_failure task_id=%s", task_id)


def _maybe_start_backlog_probe(  # noqa: C901
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
        import redis
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
                backlog_value = cast(float | int, backlog)
                QUEUE_BACKLOG.labels(**_with_base_labels(queue=queue)).set(float(backlog_value))
            time.sleep(max(interval, 1))

    with _BACKLOG_LOCK:
        if _BACKLOG_THREAD is None:
            thread = threading.Thread(target=_probe, name="queue-backlog-metrics", daemon=True)
            _BACKLOG_THREAD = thread
            thread.start()


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


def _record_task_error(task_name: str, exc: BaseException) -> None:
    labels = _with_base_labels(task=task_name, error_type=exc.__class__.__name__)
    TASK_ERRORS_TOTAL.labels(**labels).inc()


def _record_task_run(task_name: str, status: str, duration: float) -> None:
    duration = max(duration, 0.0)
    TASK_RUNS_TOTAL.labels(**_with_base_labels(task=task_name, status=status)).inc()
    TASK_DURATION_SECONDS.labels(**_with_base_labels(task=task_name)).observe(duration)


def instrument_task(task_name: str, *, emit_metrics: bool = True) -> Callable[[F], F]:
    """
    Decorator for Celery/cron/interval tasks to emit run/error/duration metrics.
    """

    def _decorator(func: F) -> F:
        if not emit_metrics:

            @functools.wraps(func)
            def _passthrough(*args: Any, **kwargs: Any) -> Any:
                return func(*args, **kwargs)

            return cast(F, _passthrough)

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def _async_wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.perf_counter()
                bind_celery_task(task_name=task_name)
                status = "success"
                try:
                    coroutine = cast(Callable[..., Awaitable[Any]], func)
                    return await coroutine(*args, **kwargs)
                except Exception as exc:
                    status = "error"
                    _record_task_error(task_name, exc)
                    raise
                finally:
                    _record_task_run(task_name, status, time.perf_counter() - start)

            return cast(F, _async_wrapper)

        @functools.wraps(func)
        def _sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            bind_celery_task(task_name=task_name)
            status = "success"
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                status = "error"
                _record_task_error(task_name, exc)
                raise
            finally:
                _record_task_run(task_name, status, time.perf_counter() - start)

        return cast(F, _sync_wrapper)

    return _decorator


@contextmanager
def record_etl_run(job: str) -> Iterator[None]:
    """Context manager capturing ETL run durations."""
    start = time.perf_counter()
    try:
        yield
    except Exception:
        _record_etl_duration(job, time.perf_counter() - start)
        record_etl_retry(job, reason="exception")
        raise
    else:
        _record_etl_duration(job, time.perf_counter() - start)


def _record_etl_duration(job: str, duration: float) -> None:
    labels = _with_base_labels(job=job or "unknown")
    ETL_RUNS_TOTAL.labels(**labels).inc()
    ETL_DURATION_SECONDS.labels(**labels).observe(max(duration, 0.0))


def record_etl_batch(job: str, *, processed: int, errors: int, duration_s: float) -> None:
    """Update per-batch ETL metrics."""
    labels = _with_base_labels(job=job or "unknown")
    if processed:
        ETL_PROCESSED_RECORDS_TOTAL.labels(**labels).inc(max(processed, 0))
    ETL_DURATION_SECONDS.labels(**labels).observe(max(duration_s, 0.0))
    if errors:
        ETL_RETRY_TOTAL.labels(**_with_base_labels(job=job or "unknown", reason="error")).inc(max(errors, 0))


def record_etl_skip(job: str) -> None:
    """Increment skip counter for ETL runs that were deduplicated."""
    _record_etl_duration(job, 0.0)
    ETL_RETRY_TOTAL.labels(**_with_base_labels(job=job or "unknown", reason="skipped")).inc()


def record_etl_retry(job: str, reason: str) -> None:
    """Increment retry counter for ETL HTTP attempts."""
    labels = _with_base_labels(job=job or "unknown", reason=(reason or "unknown"))
    ETL_RETRY_TOTAL.labels(**labels).inc()


def record_http_client_request(target: str, method: str, status_code: int | None, duration_s: float) -> None:
    """Record outbound HTTP client metrics."""
    target = (target or "unknown").lower()
    method = (method or "GET").upper()
    status_class = _status_class(status_code)
    duration = max(duration_s, 0.0)
    HTTP_CLIENT_REQUESTS_TOTAL.labels(
        **_with_base_labels(target=target, method=method, status_class=status_class)
    ).inc()
    HTTP_CLIENT_REQUEST_DURATION_SECONDS.labels(**_with_base_labels(target=target, method=method)).observe(duration)


def _status_class(status_code: int | None) -> str:
    if status_code is None:
        return "error"
    hundreds = int(status_code) // 100
    return f"{hundreds}xx"


def flush_textfile(service: str | None = None) -> Path | None:
    """Flush the shared registry to the configured textfile directory."""
    exporter = _TEXTFILE_EXPORTER
    if exporter is None:
        return None
    if service and service != exporter.service:
        exporter.service = service
    return exporter.flush()


class _TextfileExporter:
    def __init__(self, directory: Path, service: str, interval_s: float) -> None:
        self.directory = directory
        self.service = service
        self.interval_s = max(interval_s, 0.0)
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self.interval_s <= 0:
            return
        if self._thread is not None:
            return
        thread = threading.Thread(target=self._loop, name=f"metrics-textfile-{self.service}", daemon=True)
        self._thread = thread
        thread.start()

    def _loop(self) -> None:
        while not self._stop.wait(self.interval_s):
            try:
                self.flush()
            except Exception:
                logger.debug("metrics.textfile_flush_failed", exc_info=True)

    def flush(self) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"awa_{self.service}.prom"
        tmp_path = path.with_suffix(".tmp")
        payload = generate_latest(REGISTRY)
        with tmp_path.open("wb") as fh:
            fh.write(payload)
        os.replace(tmp_path, path)
        return path


def _maybe_start_textfile_exporter() -> None:
    directory = (getattr(settings, "METRICS_TEXTFILE_DIR", "") or "").strip()
    if not directory:
        return
    interval = float(getattr(settings, "METRICS_FLUSH_INTERVAL_S", 15.0) or 0.0)
    path = Path(directory)
    with _TEXTFILE_LOCK:
        exporter = _TextfileExporter(path, _SERVICE_NAME, interval)
        exporter.start()
        globals()["_TEXTFILE_EXPORTER"] = exporter


__all__ = [
    "CONTENT_TYPE_LATEST",
    "HTTP_REQUESTS_TOTAL",
    "HTTP_REQUEST_DURATION_SECONDS",
    "TASK_RUNS_TOTAL",
    "TASK_DURATION_SECONDS",
    "TASK_ERRORS_TOTAL",
    "ETL_RUNS_TOTAL",
    "ETL_PROCESSED_RECORDS_TOTAL",
    "ETL_RETRY_TOTAL",
    "ETL_DURATION_SECONDS",
    "HTTP_CLIENT_REQUESTS_TOTAL",
    "HTTP_CLIENT_REQUEST_DURATION_SECONDS",
    "QUEUE_BACKLOG",
    "MetricsMiddleware",
    "REGISTRY",
    "enable_celery_metrics",
    "flush_textfile",
    "instrument_task",
    "init",
    "on_task_failure",
    "on_task_postrun",
    "on_task_prerun",
    "record_etl_batch",
    "record_etl_run",
    "record_etl_skip",
    "record_http_client_request",
    "record_etl_retry",
    "register_metrics_endpoint",
    "start_worker_metrics_http_if_enabled",
]
