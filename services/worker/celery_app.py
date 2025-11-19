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

app_cfg = getattr(settings, "app", None)
_worker_version = getattr(settings, "APP_VERSION", getattr(app_cfg, "version", "0.0.0"))

configure_logging(service="worker", level=settings.LOG_LEVEL)
metrics_init(
    service="worker", env=(app_cfg.env if app_cfg else getattr(settings, "ENV", "local")), version=_worker_version
)


def _init_sentry() -> None:
    """Backward-compatible Sentry initializer hooking into shared helper."""
    init_sentry("worker")


_init_sentry()
structlog.get_logger(__name__).info("worker.settings", settings=settings.redacted())


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes"}


def make_celery() -> Celery:
    celery_cfg = getattr(settings, "celery", None)
    broker = os.getenv("BROKER_URL") or (celery_cfg.broker_url if celery_cfg else settings.REDIS_URL)
    backend = os.getenv("RESULT_BACKEND") or (celery_cfg.result_backend if celery_cfg else settings.REDIS_URL)
    app = Celery("awa_app", broker=broker, backend=backend)
    worker_prefetch = int(
        os.getenv("CELERY_WORKER_PREFETCH_MULTIPLIER") or (celery_cfg.prefetch_multiplier if celery_cfg else 1)
    )
    task_time_limit = int(os.getenv("CELERY_TASK_TIME_LIMIT") or (celery_cfg.task_time_limit if celery_cfg else 3600))
    store_eager = _env_bool(
        "CELERY_TASK_STORE_EAGER_RESULT", bool(celery_cfg.store_eager_result if celery_cfg else False)
    )
    result_expires = int(os.getenv("CELERY_RESULT_EXPIRES") or (celery_cfg.result_expires if celery_cfg else 86_400))
    timezone = os.getenv("TZ") or (celery_cfg.timezone if celery_cfg else "UTC")
    app.conf.update(
        task_acks_late=True,
        worker_prefetch_multiplier=worker_prefetch,
        task_time_limit=task_time_limit,
        task_default_queue="ingest",
        task_default_rate_limit=None,
        task_ignore_result=False,
        task_track_started=True,
        task_store_eager_result=store_eager,
        result_expires=result_expires,
        timezone=timezone,
        enable_utc=True,
    )
    always_eager = _env_bool("CELERY_TASK_ALWAYS_EAGER", bool(celery_cfg.always_eager if celery_cfg else False))
    if always_eager:
        app.conf.update(task_always_eager=True, task_eager_propagates=True)
    return app


celery_app = make_celery()

_beat_schedule = dict(getattr(celery_app.conf, "beat_schedule", {}) or {})


def _loop_lag_monitor_enabled() -> bool:
    celery_cfg = getattr(settings, "celery", None)
    default = bool(
        celery_cfg.loop_lag_monitor_enabled if celery_cfg else getattr(settings, "ENABLE_LOOP_LAG_MONITOR", True)
    )
    return _env_bool("CELERY_LOOP_LAG_MONITOR", default)


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
    celery_cfg = getattr(settings, "celery", None)
    interval = float(
        celery_cfg.loop_lag_interval_s
        if celery_cfg and celery_cfg.loop_lag_interval_s
        else getattr(settings, "LOOP_LAG_INTERVAL_S", 1.0) or 1.0
    )
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


def _run_alertbot_startup_validation(**_: Any) -> None:
    try:
        from services.alert_bot.worker import run_startup_validation

        run_startup_validation()
    except Exception:
        structlog.get_logger(__name__).warning("alertbot.startup_validation_failed", exc_info=True)


if getattr(getattr(settings, "observability", None), "enable_metrics", True):
    broker_url = getattr(getattr(settings, "redis", None), "broker_url", None) or settings.REDIS_URL
    redis_cfg = getattr(settings, "redis", None)
    raw_queue_names = os.getenv("QUEUE_NAMES") or getattr(settings, "QUEUE_NAMES", None)
    queue_names: list[str] | None
    if isinstance(raw_queue_names, str) and raw_queue_names.strip():
        queue_names = [item.strip() for item in raw_queue_names.split(",") if item.strip()]
    elif redis_cfg and redis_cfg.queue_names:
        queue_names = redis_cfg.queue_names
    else:
        queue_names = None
    celery_cfg = getattr(settings, "celery", None)
    raw_interval = os.getenv("BACKLOG_PROBE_SECONDS")
    if raw_interval:
        try:
            interval_s = int(raw_interval)
        except ValueError:
            interval_s = int(celery_cfg.backlog_probe_seconds if celery_cfg else 15)
    else:
        interval_s = int(celery_cfg.backlog_probe_seconds if celery_cfg else 15)
    enable_celery_metrics(
        celery_app,
        broker_url=broker_url,
        queue_names=queue_names,
        backlog_interval_s=interval_s,
    )
    start_worker_metrics_http_if_enabled()

celery_cfg = getattr(settings, "celery", None)

nightly_enabled = _env_bool(
    "SCHEDULE_NIGHTLY_MAINTENANCE",
    bool(celery_cfg.schedule_nightly_maintenance if celery_cfg else True),
)
if nightly_enabled:
    cron_expr = os.getenv("NIGHTLY_MAINTENANCE_CRON") or (
        celery_cfg.nightly_maintenance_cron if celery_cfg else "30 2 * * *"
    )
    cron = cron_expr.split()
    if len(cron) != 5:
        cron = (celery_cfg.nightly_maintenance_cron if celery_cfg else "30 2 * * *").split()
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

mv_refresh_enabled = _env_bool(
    "SCHEDULE_MV_REFRESH",
    bool(celery_cfg.schedule_mv_refresh if celery_cfg else getattr(settings, "SCHEDULE_MV_REFRESH", True)),
)
if mv_refresh_enabled:
    cron_expr = os.getenv("MV_REFRESH_CRON") or (
        celery_cfg.mv_refresh_cron if celery_cfg else getattr(settings, "MV_REFRESH_CRON", "30 2 * * *")
    )
    mv_cron = cron_expr.split()
    if len(mv_cron) != 5:
        fallback_expr = celery_cfg.mv_refresh_cron if celery_cfg else getattr(settings, "MV_REFRESH_CRON", "30 2 * * *")
        mv_cron = fallback_expr.split()
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

if celery_cfg.schedule_logistics_etl if celery_cfg else False:
    cron_expr = celery_cfg.logistics_cron if celery_cfg else "0 3 * * *"
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

base_alerts_cron = (
    os.getenv("ALERTS_EVALUATION_INTERVAL_CRON")
    or (celery_cfg.alerts_schedule_cron if celery_cfg and celery_cfg.alerts_schedule_cron else None)
    or getattr(settings, "ALERTS_EVALUATION_INTERVAL_CRON", "*/5 * * * *")
)
alerts_cron = str(base_alerts_cron)
override_minutes = os.getenv("CHECK_INTERVAL_MIN")
if override_minutes:
    try:
        minutes = max(1, int(override_minutes))
        alerts_cron = f"*/{minutes} * * * *"
    except ValueError:
        pass
elif celery_cfg and celery_cfg.alerts_check_interval_min:
    try:
        minutes = max(1, int(celery_cfg.alerts_check_interval_min))
        alerts_cron = f"*/{minutes} * * * *"
    except (TypeError, ValueError):
        pass
alerts_cron_parts = alerts_cron.split()
if len(alerts_cron_parts) != 5:
    alerts_cron_parts = "*/5 * * * *".split()
alertbot_schedule = crontab(
    minute=alerts_cron_parts[0],
    hour=alerts_cron_parts[1],
    day_of_month=alerts_cron_parts[2],
    month_of_year=alerts_cron_parts[3],
    day_of_week=alerts_cron_parts[4],
)
alertbot_entry = _beat_schedule.setdefault(
    "alertbot-run",
    {
        "task": "alertbot.run",
        "schedule": alertbot_schedule,
    },
)
_beat_schedule.setdefault("alerts-evaluate-rules", alertbot_entry)
_beat_schedule.setdefault(
    "alerts-telegram-health",
    {
        "task": "alerts.rules_health",
        "schedule": crontab(minute="0", hour="*", day_of_month="*", month_of_year="*", day_of_week="*"),
    },
)

worker_process_init.connect(_start_worker_loop_lag_monitor, weak=False)
worker_process_init.connect(_run_alertbot_startup_validation, weak=False)
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
