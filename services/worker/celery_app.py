from __future__ import annotations

import asyncio
import importlib
import os
from collections.abc import Callable
from typing import Any

import structlog
from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_process_init, worker_process_shutdown

from awa_common.logging import configure_logging
from awa_common.loop_lag import start_loop_lag_monitor
from awa_common.metrics import enable_celery_metrics, init as metrics_init, start_worker_metrics_http_if_enabled
from awa_common.sentry import init_sentry
from awa_common.settings import settings

_worker_version = getattr(settings, "APP_VERSION", "0.0.0")

configure_logging(service="worker", level=settings.LOG_LEVEL)
metrics_init(service="worker", env=settings.ENV, version=_worker_version)


def _init_sentry() -> None:
    """Backward-compatible Sentry initializer hooking into shared helper."""
    init_sentry("worker")


_init_sentry()
structlog.get_logger(__name__).info("worker.settings", settings=settings.redacted())


def make_celery() -> Celery:
    broker = settings.REDIS_URL
    backend = settings.REDIS_URL
    app = Celery("awa_app", broker=broker, backend=backend)
    app.conf.update(
        task_acks_late=True,
        worker_prefetch_multiplier=int(os.getenv("CELERY_WORKER_PREFETCH_MULTIPLIER", "1")),
        task_time_limit=int(os.getenv("CELERY_TASK_TIME_LIMIT", "3600")),
        task_default_queue="ingest",
        task_default_rate_limit=None,
        task_ignore_result=False,
        task_track_started=True,
        task_store_eager_result=(os.getenv("CELERY_TASK_STORE_EAGER_RESULT", "false").lower() in ("1", "true", "yes")),
        result_expires=int(os.getenv("CELERY_RESULT_EXPIRES", "86400")),
        timezone=os.getenv("TZ", "UTC"),
        enable_utc=True,
    )
    always_eager = os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() in (
        "1",
        "true",
        "yes",
    )
    if always_eager:
        app.conf.update(task_always_eager=True, task_eager_propagates=True)
    return app


celery_app = make_celery()

_beat_schedule = dict(getattr(celery_app.conf, "beat_schedule", {}) or {})


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in ("1", "true", "yes")


def _loop_lag_monitor_enabled() -> bool:
    raw = os.getenv("CELERY_LOOP_LAG_MONITOR")
    if raw is None:
        return True
    return raw.lower() not in {"0", "false", "no"}


_loop_lag_stop: Callable[[], None] | None = None


def is_loop_lag_monitor_active() -> bool:
    """Return True when the worker loop-lag monitor is currently running."""
    return _loop_lag_stop is not None


def _resolve_worker_loop() -> asyncio.AbstractEventLoop | None:
    policy = asyncio.get_event_loop_policy()
    try:
        loop = policy.get_event_loop()
    except RuntimeError:
        return None
    if loop.is_closed():
        return None
    return loop


def _start_worker_loop_lag_monitor(**_: Any) -> None:
    global _loop_lag_stop
    if not _loop_lag_monitor_enabled():
        return
    if _loop_lag_stop is not None:
        return
    loop = _resolve_worker_loop()
    if loop is None:
        structlog.get_logger(__name__).warning("loop_lag_monitor.loop_missing")
        return
    raw_interval = os.getenv("CELERY_LOOP_LAG_INTERVAL_S")
    if raw_interval:
        interval = float(raw_interval)
    else:
        interval = float(getattr(settings, "LOOP_LAG_INTERVAL_S", 1.0) or 1.0)
    try:
        stopper = start_loop_lag_monitor(loop, interval_s=interval)
    except Exception:
        structlog.get_logger(__name__).warning("loop_lag_monitor.start_failed", exc_info=True)
        return
    _loop_lag_stop = stopper
    structlog.get_logger(__name__).info("loop_lag_monitor.started", interval=interval)


def _stop_worker_loop_lag_monitor(**_: Any) -> None:
    global _loop_lag_stop
    stopper = _loop_lag_stop
    _loop_lag_stop = None
    if stopper is None:
        return
    try:
        stopper()
    except Exception:
        structlog.get_logger(__name__).warning("loop_lag_monitor.stop_failed", exc_info=True)


if os.getenv("ENABLE_METRICS", "1") != "0":
    broker_url = getattr(settings, "BROKER_URL", None) or settings.REDIS_URL
    queue_names_env = getattr(settings, "QUEUE_NAMES", None)
    queue_names: list[str] | None
    if isinstance(queue_names_env, str) and queue_names_env:
        queue_names = [item.strip() for item in queue_names_env.split(",") if item.strip()]
    else:
        queue_names = None
    interval_s = int(os.getenv("BACKLOG_PROBE_SECONDS", "15"))
    enable_celery_metrics(
        celery_app,
        broker_url=broker_url,
        queue_names=queue_names,
        backlog_interval_s=interval_s,
    )
    start_worker_metrics_http_if_enabled()

if os.getenv("SCHEDULE_NIGHTLY_MAINTENANCE", "true").lower() in ("1", "true", "yes"):
    cron_expr = os.getenv("NIGHTLY_MAINTENANCE_CRON", "30 2 * * *")
    cron = cron_expr.split()
    if len(cron) != 5:
        cron = "30 2 * * *".split()
    _beat_schedule["nightly-maintenance"] = {
        "task": "ingest.maintenance_nightly",
        "schedule": crontab(
            minute=cron[0],
            hour=cron[1],
            day_of_month=cron[2],
            month_of_year=cron[3],
            day_of_week=cron[4],
        ),
    }

if _env_flag("SCHEDULE_MV_REFRESH", getattr(settings, "SCHEDULE_MV_REFRESH", True)):
    cron_expr = os.getenv("MV_REFRESH_CRON", getattr(settings, "MV_REFRESH_CRON", "30 2 * * *"))
    mv_cron = cron_expr.split()
    if len(mv_cron) != 5:
        mv_cron = getattr(settings, "MV_REFRESH_CRON", "30 2 * * *").split()
    _beat_schedule["refresh-roi-fees-mvs"] = {
        "task": "db.refresh_roi_mvs",
        "schedule": crontab(
            minute=mv_cron[0],
            hour=mv_cron[1],
            day_of_month=mv_cron[2],
            month_of_year=mv_cron[3],
            day_of_week=mv_cron[4],
        ),
    }

if os.getenv("SCHEDULE_LOGISTICS_ETL", "false").lower() in ("1", "true", "yes"):
    cron_expr = os.getenv("LOGISTICS_CRON", "0 3 * * *")
    logistics_cron = cron_expr.split()
    if len(logistics_cron) != 5:
        logistics_cron = "0 3 * * *".split()
    _beat_schedule["logistics-etl-full"] = {
        "task": "logistics.etl.full",
        "schedule": crontab(
            minute=logistics_cron[0],
            hour=logistics_cron[1],
            day_of_month=logistics_cron[2],
            month_of_year=logistics_cron[3],
            day_of_week=logistics_cron[4],
        ),
    }

alerts_cron = settings.ALERTS_EVALUATION_INTERVAL_CRON or "*/5 * * * *"
legacy_minutes = os.getenv("CHECK_INTERVAL_MIN")
if legacy_minutes:
    try:
        minutes = max(1, int(legacy_minutes))
        alerts_cron = f"*/{minutes} * * * *"
    except ValueError:
        pass
alerts_cron_parts = alerts_cron.split()
if len(alerts_cron_parts) != 5:
    alerts_cron_parts = "*/5 * * * *".split()
_beat_schedule["alerts-evaluate-rules"] = {
    "task": "alerts.evaluate_rules",
    "schedule": crontab(
        minute=alerts_cron_parts[0],
        hour=alerts_cron_parts[1],
        day_of_month=alerts_cron_parts[2],
        month_of_year=alerts_cron_parts[3],
        day_of_week=alerts_cron_parts[4],
    ),
}
_beat_schedule["alerts-telegram-health"] = {
    "task": "alerts.rules_health",
    "schedule": crontab(minute="0", hour="*", day_of_month="*", month_of_year="*", day_of_week="*"),
}

worker_process_init.connect(_start_worker_loop_lag_monitor, weak=False)
worker_process_shutdown.connect(_stop_worker_loop_lag_monitor, weak=False)

if _beat_schedule:
    celery_app.conf.beat_schedule = _beat_schedule

# ensure tasks are registered
try:
    importlib.import_module("services.worker.tasks")
    importlib.import_module("services.worker.maintenance")
except Exception:
    # Optional modules may have extra dependencies; ignore failures so
    # the core application can still start.
    pass
