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
    multiproc_dir = os.getenv("PROMETHEUS_MULTIPROC_DIR") or getattr(
        getattr(settings, "observability", None), "prometheus_multiproc_dir", None
    )
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
    app_cfg = getattr(settings, "app", None)
    resolved_service = (
        service or (app_cfg.service_name if app_cfg else getattr(settings, "SERVICE_NAME", "")) or ""
    ).strip()
    if not resolved_service:
        resolved_service = "api"
    resolved_env = (
        env
        or (app_cfg.runtime_env if app_cfg else getattr(settings, "APP_ENV", None))
        or getattr(settings, "ENV", "")
        or ""
    )
    resolved_env = (resolved_env or "").strip() or "local"
    resolved_version = (version or getattr(settings, "VERSION", "") or "").strip() or "0.0.0"
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
EXTERNAL_HTTP_REQUESTS_TOTAL = Counter(
    "external_http_requests_total",
    "Outbound HTTP client request outcomes",
    ("integration", "method", "outcome", *BASE_LABELS),
    registry=REGISTRY,
)
EXTERNAL_HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "external_http_request_duration_seconds",
    "Outbound HTTP client latency in seconds",
    ("integration", "method", *BASE_LABELS),
    buckets=HTTP_BUCKETS,
    registry=REGISTRY,
)
EXTERNAL_HTTP_RETRIES_TOTAL = Counter(
    "external_http_retries_total",
    "Outbound HTTP retries grouped by reason",
    ("integration", "method", "reason", *BASE_LABELS),
    registry=REGISTRY,
)
OIDC_JWKS_REFRESH_TOTAL = Counter(
    "oidc_jwks_refresh_total",
    "JWKS refresh attempts by issuer",
    ("issuer", *BASE_LABELS),
    registry=REGISTRY,
)
OIDC_JWKS_REFRESH_FAILURES_TOTAL = Counter(
    "oidc_jwks_refresh_failures_total",
    "JWKS refresh failures by issuer",
    ("issuer", *BASE_LABELS),
    registry=REGISTRY,
)
OIDC_JWKS_AGE_SECONDS = Gauge(
    "oidc_jwks_age_seconds",
    "Age of the cached JWKS payload in seconds",
    ("issuer", *BASE_LABELS),
    registry=REGISTRY,
)
OIDC_VALIDATE_FAILURES_TOTAL = Counter(
    "oidc_validate_failures_total",
    "OIDC validation failures grouped by reason",
    ("reason", *BASE_LABELS),
    registry=REGISTRY,
)
HTTP_429_TOTAL = Counter(
    "http_429_total",
    "HTTP 429 responses grouped by route and role",
    ("route", "role", *BASE_LABELS),
    registry=REGISTRY,
)
AWA_INGEST_UPLOAD_BYTES_TOTAL = Counter(
    "awa_ingest_upload_bytes_total",
    "Bytes accepted by /upload and /ingest streaming flows",
    ("extension", *BASE_LABELS),
    registry=REGISTRY,
)
AWA_INGEST_UPLOAD_SECONDS = Histogram(
    "awa_ingest_upload_seconds",
    "Upload handling latency in seconds",
    ("extension", *BASE_LABELS),
    buckets=HTTP_BUCKETS,
    registry=REGISTRY,
)
AWA_INGEST_UPLOAD_INFLIGHT = Gauge(
    "awa_ingest_upload_inflight",
    "Concurrent uploads being processed",
    (*BASE_LABELS,),
    registry=REGISTRY,
)
AWA_INGEST_UPLOAD_FAILURES_TOTAL = Counter(
    "awa_ingest_upload_failures_total",
    "Upload failures for streaming endpoints",
    ("extension", "reason", *BASE_LABELS),
    registry=REGISTRY,
)
AWA_INGEST_TASK_OUTCOME_TOTAL = Counter(
    "awa_ingest_task_outcome_total",
    "Ingest task executions grouped by status",
    ("task", "status", *BASE_LABELS),
    registry=REGISTRY,
)
AWA_INGEST_TASK_SECONDS = Histogram(
    "awa_ingest_task_seconds",
    "Ingest task runtime in seconds",
    ("task", "status", *BASE_LABELS),
    buckets=HTTP_BUCKETS,
    registry=REGISTRY,
)
AWA_INGEST_TASK_FAILURES_TOTAL = Counter(
    "awa_ingest_task_failures_total",
    "Ingest task failures grouped by error type",
    ("task", "error_type", *BASE_LABELS),
    registry=REGISTRY,
)
API_INGEST_4XX_TOTAL = Counter(
    "api_ingest_4xx_total",
    "ETL ingest API 4xx responses grouped by error code",
    ("code", *BASE_LABELS),
    registry=REGISTRY,
)
API_INGEST_5XX_TOTAL = Counter(
    "api_ingest_5xx_total",
    "ETL ingest API 5xx responses",
    (*BASE_LABELS,),
    registry=REGISTRY,
)
AWA_RETRY_ATTEMPTS_TOTAL = Counter(
    "awa_retry_attempts_total",
    "Retry attempts grouped by operation",
    ("operation", *BASE_LABELS),
    registry=REGISTRY,
)
AWA_RETRY_SLEEP_SECONDS = Histogram(
    "awa_retry_sleep_seconds",
    "Sleep duration before retry attempts",
    ("operation", *BASE_LABELS),
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
ETL_ROW_NORMALIZED_TOTAL = Counter(
    "etl_row_normalized_total",
    "Normalized row counts per ETL job",
    ("job", *BASE_LABELS),
    registry=REGISTRY,
)
ETL_NORMALIZE_ERRORS_TOTAL = Counter(
    "etl_normalize_errors_total",
    "Normalization errors grouped by job and reason",
    ("job", "reason", *BASE_LABELS),
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
LOGISTICS_ETL_TASKS_INFLIGHT = Gauge(
    "logistics_etl_tasks_inflight",
    "Concurrent logistics ETL sources being processed",
    ("source", *BASE_LABELS),
    registry=REGISTRY,
)
LOGISTICS_ETL_TASK_SECONDS = Histogram(
    "logistics_etl_task_seconds",
    "Per-source logistics ETL duration in seconds",
    ("source", *BASE_LABELS),
    buckets=HTTP_BUCKETS,
    registry=REGISTRY,
)
LOGISTICS_ETL_ROWS_TOTAL = Counter(
    "logistics_etl_rows_total",
    "Rows handled per logistics ETL source",
    ("source", "result", *BASE_LABELS),
    registry=REGISTRY,
)
LOGISTICS_ETL_ERRORS_TOTAL = Counter(
    "logistics_etl_errors_total",
    "Errors raised per logistics ETL source",
    ("source", "reason", *BASE_LABELS),
    registry=REGISTRY,
)
LOGISTICS_UPSERT_ROWS_TOTAL = Counter(
    "logistics_upsert_rows_total",
    "Rows affected by batched logistics upserts",
    ("operation", *BASE_LABELS),
    registry=REGISTRY,
)
LOGISTICS_UPSERT_BATCH_SECONDS = Histogram(
    "logistics_upsert_batch_seconds",
    "Duration of batched logistics upserts in seconds",
    (*BASE_LABELS,),
    buckets=HTTP_BUCKETS,
    registry=REGISTRY,
)
AWA_INGEST_DOWNLOAD_BYTES_TOTAL = Counter(
    "awa_ingest_download_bytes_total",
    "Bytes downloaded for ingest URIs",
    ("scheme", *BASE_LABELS),
    registry=REGISTRY,
)
AWA_INGEST_DOWNLOAD_SECONDS = Histogram(
    "awa_ingest_download_seconds",
    "Download latency for ingest URIs",
    ("scheme", *BASE_LABELS),
    buckets=HTTP_BUCKETS,
    registry=REGISTRY,
)
AWA_INGEST_DOWNLOAD_FAILURES_TOTAL = Counter(
    "awa_ingest_download_failures_total",
    "Download failures by URI scheme",
    ("scheme", "reason", *BASE_LABELS),
    registry=REGISTRY,
)
AWA_REDIS_ERRORS_TOTAL = Counter(
    "awa_redis_errors_total",
    "Redis command failures grouped by operation and command",
    ("operation", "command", "key", *BASE_LABELS),
    registry=REGISTRY,
)
STATS_CACHE_HITS_TOTAL = Counter(
    "stats_cache_hits_total",
    "Cache hits for /stats endpoints",
    ("endpoint", *BASE_LABELS),
    registry=REGISTRY,
)
STATS_CACHE_MISS_TOTAL = Counter(
    "stats_cache_miss_total",
    "Cache misses for /stats endpoints",
    ("endpoint", *BASE_LABELS),
    registry=REGISTRY,
)
STATS_QUERY_DURATION_SECONDS = Histogram(
    "stats_query_duration_seconds",
    "Execution time of stats SQL queries",
    ("endpoint", *BASE_LABELS),
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
ALERTS_SENT_TOTAL = Counter(
    "alerts_sent_total",
    "Alert notifications attempted by channel and outcome",
    ("rule", "severity", "channel", "status", *BASE_LABELS),
    registry=REGISTRY,
)
ALERT_RULE_SKIPPED_TOTAL = Counter(
    "alert_rule_skipped_total",
    "Alert rules skipped before sending",
    ("rule", "reason", *BASE_LABELS),
    registry=REGISTRY,
)
ALERT_ERRORS_TOTAL = Counter(
    "alert_errors_total",
    "Alert pipeline errors grouped by type",
    ("rule", "type", *BASE_LABELS),
    registry=REGISTRY,
)
ALERTBOT_RULES_EVALUATED_TOTAL = Counter(
    "alertbot_rules_evaluated_total",
    "Alert bot rule evaluations by outcome",
    ("rule", "outcome", *BASE_LABELS),
    registry=REGISTRY,
)
ALERTBOT_EVENTS_EMITTED_TOTAL = Counter(
    "alertbot_events_emitted_total",
    "Alert events emitted by rule",
    ("rule", *BASE_LABELS),
    registry=REGISTRY,
)
ALERTBOT_MESSAGES_SENT_TOTAL = Counter(
    "alertbot_messages_sent_total",
    "Telegram messages attempted by rule and status",
    ("rule", "status", *BASE_LABELS),
    registry=REGISTRY,
)
ALERTBOT_TELEGRAM_ERRORS_TOTAL = Counter(
    "alertbot_telegram_errors_total",
    "Telegram API errors grouped by error_code",
    ("error_code", *BASE_LABELS),
    registry=REGISTRY,
)
ALERTBOT_RULE_EVAL_DURATION_SECONDS = Histogram(
    "alertbot_rule_eval_duration_seconds",
    "Latency for evaluating a single alert rule",
    ("rule", *BASE_LABELS),
    buckets=HTTP_BUCKETS,
    registry=REGISTRY,
)
ALERTBOT_SEND_LATENCY_SECONDS = Histogram(
    "alertbot_send_latency_seconds",
    "Latency for sending Telegram messages",
    (*BASE_LABELS,),
    buckets=HTTP_BUCKETS,
    registry=REGISTRY,
)
ALERTBOT_BATCH_DURATION_SECONDS = Histogram(
    "alertbot_batch_duration_seconds",
    "Latency for completing a full alert bot batch",
    (*BASE_LABELS,),
    buckets=HTTP_BUCKETS,
    registry=REGISTRY,
)
ALERTBOT_INFLIGHT_SENDS = Gauge(
    "alertbot_inflight_sends",
    "Number of in-flight Telegram send operations",
    (*BASE_LABELS,),
    registry=REGISTRY,
)
ALERTBOT_STARTUP_VALIDATION_OK = Gauge(
    "alertbot_startup_validation_ok",
    "Whether alert bot startup validation succeeded (1) or not (0)",
    (*BASE_LABELS,),
    registry=REGISTRY,
)
EVENT_LOOP_LAG_SECONDS = Gauge(
    "event_loop_lag_seconds",
    "Observed event loop scheduling lag",
    (*BASE_LABELS,),
    registry=REGISTRY,
)
PRICE_IMPORTER_VALIDATE_SECONDS = Histogram(
    "price_importer_validate_seconds",
    "Time spent validating and normalising price importer chunks",
    (*BASE_LABELS,),
    buckets=HTTP_BUCKETS,
    registry=REGISTRY,
)
PRICE_IMPORTER_ROWS_TOTAL = Counter(
    "price_importer_rows_total",
    "Rows processed by the price importer",
    ("stage", *BASE_LABELS),
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
    """Start HTTP exporter for worker metrics if enabled via configuration/env."""
    raw_flag = os.getenv("WORKER_METRICS_HTTP")
    observability = getattr(settings, "observability", None)
    if raw_flag is not None:
        enabled = raw_flag in {"1", "true", "TRUE"}
    else:
        enabled = bool(observability and observability.worker_metrics_http)
    if not enabled:
        return
    raw_port = os.getenv(port_env)
    if raw_port is not None:
        try:
            port = int(raw_port)
        except ValueError:
            port = 9108
    else:
        port = int(observability.worker_metrics_port if observability else 9108)
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


def record_etl_rows_normalized(job: str, rows: int) -> None:
    if rows <= 0:
        return
    labels = _with_base_labels(job=job or "unknown")
    ETL_ROW_NORMALIZED_TOTAL.labels(**labels).inc(max(rows, 0))


def record_etl_normalize_error(job: str, reason: str, count: int = 1) -> None:
    if count <= 0:
        return
    labels = _with_base_labels(job=job or "unknown", reason=(reason or "unknown"))
    ETL_NORMALIZE_ERRORS_TOTAL.labels(**labels).inc(max(count, 0))


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


def record_external_http_request(integration: str, method: str, outcome: str) -> None:
    """Record shared HTTP client outcomes."""
    labels = _with_base_labels(
        integration=(integration or "default").strip().lower() or "default",
        method=(method or "GET").upper(),
        outcome=(outcome or "error").strip().lower(),
    )
    EXTERNAL_HTTP_REQUESTS_TOTAL.labels(**labels).inc()


def observe_external_http_latency(integration: str, method: str, duration_s: float) -> None:
    """Record shared HTTP client latency."""
    labels = _with_base_labels(
        integration=(integration or "default").strip().lower() or "default",
        method=(method or "GET").upper(),
    )
    EXTERNAL_HTTP_REQUEST_DURATION_SECONDS.labels(**labels).observe(max(duration_s, 0.0))


def record_external_http_retry(integration: str, method: str, reason: str) -> None:
    """Record retry attempts performed by the shared HTTP client."""
    labels = _with_base_labels(
        integration=(integration or "default").strip().lower() or "default",
        method=(method or "GET").upper(),
        reason=(reason or "error").strip().lower(),
    )
    EXTERNAL_HTTP_RETRIES_TOTAL.labels(**labels).inc()


def _status_class(status_code: int | None) -> str:
    if status_code is None:
        return "error"
    hundreds = int(status_code) // 100
    return f"{hundreds}xx"


@contextmanager
def ingest_upload_inflight() -> Iterator[None]:
    labels = _with_base_labels()
    AWA_INGEST_UPLOAD_INFLIGHT.labels(**labels).inc()
    try:
        yield
    finally:
        AWA_INGEST_UPLOAD_INFLIGHT.labels(**labels).dec()


def _upload_labels(extension: str | None) -> dict[str, str]:
    ext = (extension or "unknown").lstrip(".") or "unknown"
    return _with_base_labels(extension=ext)


def record_ingest_upload(bytes_count: int, duration_s: float, *, extension: str | None) -> None:
    labels = _upload_labels(extension)
    if bytes_count > 0:
        AWA_INGEST_UPLOAD_BYTES_TOTAL.labels(**labels).inc(max(bytes_count, 0))
    AWA_INGEST_UPLOAD_SECONDS.labels(**labels).observe(max(duration_s, 0.0))


def record_ingest_upload_failure(*, extension: str | None, reason: str) -> None:
    labels = _with_base_labels(extension=(extension or "unknown").lstrip(".") or "unknown", reason=reason or "error")
    AWA_INGEST_UPLOAD_FAILURES_TOTAL.labels(**labels).inc()


def _ingest_task_labels(task: str, status: str) -> dict[str, str]:
    task_label = (task or "unknown").strip() or "unknown"
    status_label = (status or "unknown").strip() or "unknown"
    return _with_base_labels(task=task_label, status=status_label)


def record_ingest_task_outcome(task: str, *, success: bool, duration_s: float) -> None:
    status = "success" if success else "error"
    labels = _ingest_task_labels(task, status)
    AWA_INGEST_TASK_OUTCOME_TOTAL.labels(**labels).inc()
    AWA_INGEST_TASK_SECONDS.labels(**labels).observe(max(duration_s, 0.0))


def record_ingest_task_failure(task: str, exc: BaseException) -> None:
    task_label = (task or "unknown").strip() or "unknown"
    error_type = getattr(exc, "__class__", type(exc)).__name__
    labels = _with_base_labels(task=task_label, error_type=error_type or "unknown")
    AWA_INGEST_TASK_FAILURES_TOTAL.labels(**labels).inc()


def logistics_source_label(source: str | None) -> str:
    label = (source or "unknown").strip() or "unknown"
    if len(label) > 80:
        return label[:80]
    return label


def logistics_source_labels(source: str | None) -> dict[str, str]:
    return _with_base_labels(source=logistics_source_label(source))


def record_logistics_rows(source: str | None, *, rows: int, result: str) -> None:
    if rows <= 0:
        return
    labels = _with_base_labels(source=logistics_source_label(source), result=(result or "processed"))
    LOGISTICS_ETL_ROWS_TOTAL.labels(**labels).inc(max(rows, 0))


def record_logistics_error(source: str | None, reason: str) -> None:
    labels = _with_base_labels(source=logistics_source_label(source), reason=(reason or "unknown"))
    LOGISTICS_ETL_ERRORS_TOTAL.labels(**labels).inc()


def record_logistics_task_duration(source: str | None, duration_s: float) -> None:
    labels = logistics_source_labels(source)
    LOGISTICS_ETL_TASK_SECONDS.labels(**labels).observe(max(duration_s, 0.0))


def logistics_task_inflight_change(source: str | None, delta: int) -> None:
    labels = logistics_source_labels(source)
    if delta >= 0:
        LOGISTICS_ETL_TASKS_INFLIGHT.labels(**labels).inc(delta)
    else:
        LOGISTICS_ETL_TASKS_INFLIGHT.labels(**labels).dec(abs(delta))


def record_logistics_upsert_rows(operation: str, rows: int) -> None:
    if rows <= 0:
        return
    labels = _with_base_labels(operation=(operation or "unknown"))
    LOGISTICS_UPSERT_ROWS_TOTAL.labels(**labels).inc(max(rows, 0))


def record_logistics_upsert_batch(duration_s: float) -> None:
    LOGISTICS_UPSERT_BATCH_SECONDS.labels(**_with_base_labels()).observe(max(duration_s, 0.0))


def record_price_importer_rows(stage: str, rows: int) -> None:
    if rows <= 0:
        return
    labels = _with_base_labels(stage=(stage or "unknown"))
    PRICE_IMPORTER_ROWS_TOTAL.labels(**labels).inc(max(rows, 0))


def record_price_importer_validation(duration_s: float) -> None:
    PRICE_IMPORTER_VALIDATE_SECONDS.labels(**_with_base_labels()).observe(max(duration_s, 0.0))


def _stats_labels(endpoint: str) -> dict[str, str]:
    label = (endpoint or "unknown").lower() or "unknown"
    return _with_base_labels(endpoint=label)


def record_stats_cache_hit(endpoint: str) -> None:
    STATS_CACHE_HITS_TOTAL.labels(**_stats_labels(endpoint)).inc()


def record_stats_cache_miss(endpoint: str) -> None:
    STATS_CACHE_MISS_TOTAL.labels(**_stats_labels(endpoint)).inc()


def record_stats_query_duration(endpoint: str, duration_s: float) -> None:
    STATS_QUERY_DURATION_SECONDS.labels(**_stats_labels(endpoint)).observe(max(duration_s, 0.0))


def record_ingest_download(bytes_count: int, duration_s: float, *, scheme: str | None) -> None:
    label = (scheme or "unknown").lower() or "unknown"
    labels = _with_base_labels(scheme=label)
    if bytes_count > 0:
        AWA_INGEST_DOWNLOAD_BYTES_TOTAL.labels(**labels).inc(max(bytes_count, 0))
    AWA_INGEST_DOWNLOAD_SECONDS.labels(**labels).observe(max(duration_s, 0.0))


def record_ingest_download_failure(*, scheme: str | None, reason: str) -> None:
    scheme_label = (scheme or "unknown").lower() or "unknown"
    labels = _with_base_labels(scheme=scheme_label, reason=reason or "error")
    AWA_INGEST_DOWNLOAD_FAILURES_TOTAL.labels(**labels).inc()


def _redis_key_label(key: str | None) -> str:
    raw = (key or "unknown").strip()
    if not raw:
        return "unknown"
    if ":" in raw:
        prefix = raw.split(":", 1)[0]
        return f"{prefix}:*"
    if len(raw) > 48:
        return raw[:48]
    return raw


def record_redis_error(operation: str, command: str, *, key: str | None = None) -> None:
    labels = _with_base_labels(
        operation=(operation or "unknown").strip() or "unknown",
        command=(command or "unknown").strip() or "unknown",
        key=_redis_key_label(key),
    )
    AWA_REDIS_ERRORS_TOTAL.labels(**labels).inc()


def record_api_ingest_4xx_total(code: str) -> None:
    label = (code or "unknown").strip() or "unknown"
    API_INGEST_4XX_TOTAL.labels(**_with_base_labels(code=label)).inc()


def record_api_ingest_5xx_total() -> None:
    API_INGEST_5XX_TOTAL.labels(**_with_base_labels()).inc()


def record_retry_attempt(operation: str) -> None:
    label = (operation or "unknown").strip().lower() or "unknown"
    AWA_RETRY_ATTEMPTS_TOTAL.labels(**_with_base_labels(operation=label)).inc()


def record_retry_sleep(operation: str, seconds: float | None) -> None:
    label = (operation or "unknown").strip().lower() or "unknown"
    duration = max(float(seconds or 0.0), 0.0)
    AWA_RETRY_SLEEP_SECONDS.labels(**_with_base_labels(operation=label)).observe(duration)


def record_oidc_jwks_refresh(
    issuer: str,
    *,
    success: bool,
    age_seconds: float | None = None,
    count: bool = True,
) -> None:
    """Track JWKS refresh attempts plus cache age.

    Set ``count=False`` to update the gauge without incrementing the counters.
    """
    issuer_label = (issuer or "unknown").strip() or "unknown"
    labels = _with_base_labels(issuer=issuer_label)
    if count:
        OIDC_JWKS_REFRESH_TOTAL.labels(**labels).inc()
        if not success:
            OIDC_JWKS_REFRESH_FAILURES_TOTAL.labels(**labels).inc()
    if age_seconds is not None:
        OIDC_JWKS_AGE_SECONDS.labels(**labels).set(max(age_seconds, 0.0))


def record_oidc_validation_failure(reason: str) -> None:
    """Increment validation failure counter with a normalised reason."""
    label = (reason or "unknown").lower() or "unknown"
    OIDC_VALIDATE_FAILURES_TOTAL.labels(**_with_base_labels(reason=label)).inc()


def record_http_429(route: str, role: str) -> None:
    """Record HTTP 429 responses by route template and caller role."""
    route_label = (route or "unknown").strip() or "unknown"
    role_label = (role or "unknown").strip().lower() or "unknown"
    HTTP_429_TOTAL.labels(**_with_base_labels(route=route_label, role=role_label)).inc()


async def monitor_event_loop_lag(interval_s: float = 0.5, *, warn_threshold_s: float | None = None) -> None:
    """Track event loop scheduling delay."""
    loop = asyncio.get_running_loop()
    labels = _with_base_labels()
    try:
        while True:
            start = loop.time()
            await asyncio.sleep(interval_s)
            lag = max(loop.time() - start - interval_s, 0.0)
            EVENT_LOOP_LAG_SECONDS.labels(**labels).set(lag)
            if warn_threshold_s is not None and lag > warn_threshold_s:
                logger.warning("event_loop.lag lag_ms=%d", int(lag * 1000))
    except asyncio.CancelledError:  # pragma: no cover - shutdown path
        EVENT_LOOP_LAG_SECONDS.labels(**labels).set(0.0)
        raise


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
    "HTTP_429_TOTAL",
    "AWA_INGEST_UPLOAD_BYTES_TOTAL",
    "AWA_INGEST_UPLOAD_SECONDS",
    "AWA_INGEST_UPLOAD_INFLIGHT",
    "AWA_INGEST_UPLOAD_FAILURES_TOTAL",
    "AWA_INGEST_TASK_OUTCOME_TOTAL",
    "AWA_INGEST_TASK_SECONDS",
    "AWA_INGEST_TASK_FAILURES_TOTAL",
    "API_INGEST_4XX_TOTAL",
    "API_INGEST_5XX_TOTAL",
    "AWA_RETRY_ATTEMPTS_TOTAL",
    "AWA_RETRY_SLEEP_SECONDS",
    "TASK_RUNS_TOTAL",
    "TASK_DURATION_SECONDS",
    "TASK_ERRORS_TOTAL",
    "ETL_RUNS_TOTAL",
    "ETL_PROCESSED_RECORDS_TOTAL",
    "ETL_ROW_NORMALIZED_TOTAL",
    "ETL_NORMALIZE_ERRORS_TOTAL",
    "ETL_RETRY_TOTAL",
    "ETL_DURATION_SECONDS",
    "LOGISTICS_ETL_TASKS_INFLIGHT",
    "LOGISTICS_ETL_TASK_SECONDS",
    "LOGISTICS_ETL_ROWS_TOTAL",
    "LOGISTICS_ETL_ERRORS_TOTAL",
    "LOGISTICS_UPSERT_ROWS_TOTAL",
    "LOGISTICS_UPSERT_BATCH_SECONDS",
    "AWA_INGEST_DOWNLOAD_BYTES_TOTAL",
    "AWA_INGEST_DOWNLOAD_SECONDS",
    "AWA_INGEST_DOWNLOAD_FAILURES_TOTAL",
    "AWA_REDIS_ERRORS_TOTAL",
    "HTTP_CLIENT_REQUESTS_TOTAL",
    "HTTP_CLIENT_REQUEST_DURATION_SECONDS",
    "EXTERNAL_HTTP_REQUESTS_TOTAL",
    "EXTERNAL_HTTP_REQUEST_DURATION_SECONDS",
    "EXTERNAL_HTTP_RETRIES_TOTAL",
    "OIDC_JWKS_REFRESH_TOTAL",
    "OIDC_JWKS_REFRESH_FAILURES_TOTAL",
    "OIDC_JWKS_AGE_SECONDS",
    "OIDC_VALIDATE_FAILURES_TOTAL",
    "QUEUE_BACKLOG",
    "EVENT_LOOP_LAG_SECONDS",
    "PRICE_IMPORTER_VALIDATE_SECONDS",
    "PRICE_IMPORTER_ROWS_TOTAL",
    "MetricsMiddleware",
    "REGISTRY",
    "enable_celery_metrics",
    "flush_textfile",
    "ingest_upload_inflight",
    "logistics_source_label",
    "logistics_source_labels",
    "logistics_task_inflight_change",
    "monitor_event_loop_lag",
    "instrument_task",
    "init",
    "on_task_failure",
    "on_task_postrun",
    "on_task_prerun",
    "record_etl_batch",
    "record_etl_run",
    "record_etl_skip",
    "record_etl_rows_normalized",
    "record_etl_normalize_error",
    "record_ingest_upload",
    "record_ingest_upload_failure",
    "record_ingest_task_outcome",
    "record_ingest_task_failure",
    "record_ingest_download",
    "record_ingest_download_failure",
    "record_redis_error",
    "record_api_ingest_4xx_total",
    "record_api_ingest_5xx_total",
    "record_retry_attempt",
    "record_retry_sleep",
    "record_oidc_jwks_refresh",
    "record_oidc_validation_failure",
    "record_http_429",
    "record_http_client_request",
    "record_external_http_request",
    "observe_external_http_latency",
    "record_external_http_retry",
    "record_logistics_rows",
    "record_logistics_error",
    "record_logistics_task_duration",
    "record_etl_retry",
    "record_logistics_upsert_rows",
    "record_logistics_upsert_batch",
    "record_price_importer_rows",
    "record_price_importer_validation",
    "register_metrics_endpoint",
    "start_worker_metrics_http_if_enabled",
]
