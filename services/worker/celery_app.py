from __future__ import annotations

import asyncio
import importlib
from collections.abc import Callable
from typing import Any

import structlog
from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_process_init, worker_process_shutdown
from pydantic import ValidationError

from awa_common.configuration import CelerySettings
from awa_common.cron_config import CronConfigError, CronSchedule
from awa_common.logging import configure_logging
from awa_common.loop_lag import start_loop_lag_monitor
from awa_common.metrics import enable_celery_metrics, init as metrics_init, start_worker_metrics_http_if_enabled
from awa_common.sentry import init_sentry
from awa_common.settings import settings
from awa_common.utils.env import env_bool

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
logger = structlog.get_logger(__name__)
logger.info("worker.settings", settings=settings.redacted())


def _get_celery_cfg() -> CelerySettings | None:
    """Return a fresh Celery settings snapshot."""
    settings.__dict__.pop("celery", None)
    cfg = getattr(settings, "celery", None)
    return cfg if isinstance(cfg, CelerySettings) else None


def make_celery() -> Celery:
    celery_cfg = _get_celery_cfg()
    broker = celery_cfg.broker_url if celery_cfg else (settings.BROKER_URL or settings.REDIS_URL)
    backend = celery_cfg.result_backend if celery_cfg else (settings.RESULT_BACKEND or settings.REDIS_URL)
    app = Celery("awa_app", broker=broker, backend=backend)
    worker_prefetch = int(celery_cfg.prefetch_multiplier if celery_cfg else settings.CELERY_WORKER_PREFETCH_MULTIPLIER)
    task_time_limit = int(celery_cfg.task_time_limit if celery_cfg else settings.CELERY_TASK_TIME_LIMIT)
    store_eager = env_bool(
        "CELERY_TASK_STORE_EAGER_RESULT",
        default=bool(celery_cfg.store_eager_result if celery_cfg else settings.CELERY_TASK_STORE_EAGER_RESULT),
    )
    result_expires = int(celery_cfg.result_expires if celery_cfg else settings.CELERY_RESULT_EXPIRES)
    timezone = celery_cfg.timezone if celery_cfg else settings.TZ
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
    always_eager = env_bool(
        "CELERY_TASK_ALWAYS_EAGER",
        default=bool(celery_cfg.always_eager if celery_cfg else settings.CELERY_TASK_ALWAYS_EAGER),
    )
    if always_eager:
        app.conf.update(task_always_eager=True, task_eager_propagates=True)
    return app


celery_app = make_celery()

_beat_schedule = dict(getattr(celery_app.conf, "beat_schedule", {}) or {})


def _register_cron_schedule(
    entry_name: str,
    *,
    task: str,
    expression: str,
    setting_name: str,
) -> None:
    try:
        schedule = CronSchedule(name=setting_name, expression=expression).as_crontab()
    except (CronConfigError, ValidationError) as exc:
        logger.error(
            "worker.invalid_cron_config",
            job=entry_name,
            task=task,
            setting=setting_name,
            cron=expression,
            error=str(exc),
        )
        raise RuntimeError(f"{setting_name} value {expression!r} is not a valid cron expression.") from exc
    _beat_schedule[entry_name] = {
        "task": task,
        "schedule": schedule,
    }


def _resolve_alertbot_cron_expression() -> str:
    base_expr = getattr(settings, "ALERTS_EVALUATION_INTERVAL_CRON", "*/5 * * * *")
    override_minutes = getattr(settings, "CHECK_INTERVAL_MIN", None)
    if override_minutes is not None:
        try:
            minutes = max(1, int(override_minutes))
            return f"*/{minutes} * * * *"
        except (TypeError, ValueError):
            logger.warning("worker.alerts.invalid_interval_override", value=override_minutes)
    return base_expr


def _loop_lag_monitor_enabled() -> bool:
    celery_cfg = _get_celery_cfg()
    default = bool(
        celery_cfg.loop_lag_monitor_enabled
        if celery_cfg
        else getattr(settings, "CELERY_LOOP_LAG_MONITOR", getattr(settings, "ENABLE_LOOP_LAG_MONITOR", True))
    )
    return bool(env_bool("CELERY_LOOP_LAG_MONITOR", default=default))


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
    raw_queue_names = getattr(settings, "QUEUE_NAMES", None)
    queue_names: list[str] | None = None
    if isinstance(raw_queue_names, str) and raw_queue_names.strip():
        queue_names = [item.strip() for item in raw_queue_names.split(",") if item.strip()]
    elif redis_cfg and redis_cfg.queue_names:
        queue_names = list(redis_cfg.queue_names)
    celery_cfg = _get_celery_cfg()
    interval_s = int(celery_cfg.backlog_probe_seconds if celery_cfg else getattr(settings, "BACKLOG_PROBE_SECONDS", 15))
    enable_celery_metrics(
        celery_app,
        broker_url=broker_url,
        queue_names=queue_names,
        backlog_interval_s=interval_s,
    )
    start_worker_metrics_http_if_enabled()

nested_celery_cfg = _get_celery_cfg()

nightly_enabled = env_bool(
    "SCHEDULE_NIGHTLY_MAINTENANCE",
    default=bool(
        getattr(nested_celery_cfg, "schedule_nightly_maintenance", None)
        if nested_celery_cfg
        else getattr(settings, "SCHEDULE_NIGHTLY_MAINTENANCE", True)
    ),
)
if nightly_enabled:
    cron_expr = str(
        getattr(nested_celery_cfg, "nightly_maintenance_cron", None)
        or getattr(settings, "NIGHTLY_MAINTENANCE_CRON", "30 2 * * *")
    )
    _register_cron_schedule(
        "nightly-maintenance",
        task="ingest.maintenance_nightly",
        expression=cron_expr,
        setting_name="NIGHTLY_MAINTENANCE_CRON",
    )

mv_refresh_enabled = env_bool(
    "SCHEDULE_MV_REFRESH",
    default=bool(
        getattr(nested_celery_cfg, "schedule_mv_refresh", None)
        if nested_celery_cfg
        else getattr(settings, "SCHEDULE_MV_REFRESH", True)
    ),
)
if mv_refresh_enabled:
    cron_expr = str(
        getattr(nested_celery_cfg, "mv_refresh_cron", None) or getattr(settings, "MV_REFRESH_CRON", "30 2 * * *")
    )
    _register_cron_schedule(
        "refresh-roi-fees-mvs",
        task="db.refresh_roi_mvs",
        expression=cron_expr,
        setting_name="MV_REFRESH_CRON",
    )

logistics_enabled = env_bool(
    "SCHEDULE_LOGISTICS_ETL",
    default=bool(
        getattr(nested_celery_cfg, "schedule_logistics_etl", None)
        if nested_celery_cfg
        else getattr(settings, "SCHEDULE_LOGISTICS_ETL", False)
    ),
)
if logistics_enabled:
    cron_expr = str(
        getattr(nested_celery_cfg, "logistics_cron", None) or getattr(settings, "LOGISTICS_CRON", "0 3 * * *")
    )
    _register_cron_schedule(
        "logistics-etl-full",
        task="logistics.etl.full",
        expression=cron_expr,
        setting_name="LOGISTICS_CRON",
    )

alerts_cron_expr = _resolve_alertbot_cron_expression()
_register_cron_schedule(
    "alertbot-run",
    task="alertbot.run",
    expression=alerts_cron_expr,
    setting_name="ALERTS_EVALUATION_INTERVAL_CRON",
)
alertbot_entry = _beat_schedule["alertbot-run"]
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
