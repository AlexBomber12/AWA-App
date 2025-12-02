from __future__ import annotations

import asyncio
import importlib
import os
from collections.abc import Callable
from dataclasses import dataclass
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
    redis_cfg = getattr(settings, "redis", None)
    env_broker = os.getenv("BROKER_URL") or os.getenv("CELERY_BROKER_URL")
    env_backend = os.getenv("RESULT_BACKEND") or os.getenv("CELERY_RESULT_BACKEND")
    broker = (
        env_broker or celery_cfg.broker_url
        if celery_cfg
        else (redis_cfg.broker_url if redis_cfg else (settings.BROKER_URL or settings.REDIS_URL))
    )
    backend = (
        env_backend or celery_cfg.result_backend
        if celery_cfg
        else (settings.RESULT_BACKEND or (redis_cfg.url if redis_cfg else settings.REDIS_URL))
    )
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


@dataclass(slots=True, frozen=True)
class BeatScheduleEntry:
    name: str
    task: str
    setting_name: str
    expression: str


def _validate_cron_entries(entries: list[BeatScheduleEntry]) -> list[tuple[str, str, Any]]:
    """Validate cron expressions once and build Celery schedules."""

    errors: list[str] = []
    compiled: list[tuple[str, str, Any]] = []
    for entry in entries:
        try:
            schedule = CronSchedule(name=entry.setting_name, expression=entry.expression).as_crontab()
        except (CronConfigError, ValidationError) as exc:
            logger.error(
                "worker.invalid_cron_config",
                job=entry.name,
                task=entry.task,
                setting=entry.setting_name,
                cron=entry.expression,
                error=str(exc),
            )
            errors.append(entry.setting_name)
            continue
        compiled.append((entry.name, entry.task, schedule))
    if errors:
        settings_list = ", ".join(sorted(set(errors)))
        raise RuntimeError(f"Invalid cron configuration for: {settings_list}")
    return compiled


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
    logger = structlog.get_logger(__name__)
    try:
        module = importlib.import_module("services.alert_bot.worker")
    except Exception:
        logger.warning("alertbot.startup_validation_failed", exc_info=True)
        return
    run_startup_validation = getattr(module, "run_startup_validation", None)
    alert_error = getattr(module, "AlertConfigurationError", None)
    if not callable(run_startup_validation):
        logger.warning("alertbot.startup_validation_missing")
        return
    try:
        run_startup_validation()
    except SystemExit as exc:
        logger.error("alertbot.startup_validation_failed", fatal=True, error=str(exc))
        raise
    except Exception as exc:
        if alert_error is not None and isinstance(exc, alert_error):
            logger.error("alertbot.startup_validation_failed", fatal=True, error=str(exc))
            raise
        logger.warning("alertbot.startup_validation_failed", exc_info=True)


if getattr(getattr(settings, "observability", None), "enable_metrics", True):
    redis_cfg = getattr(settings, "redis", None)
    broker_url = redis_cfg.broker_url if redis_cfg else settings.REDIS_URL
    env_broker = os.getenv("BROKER_URL") or os.getenv("CELERY_BROKER_URL")
    if env_broker:
        broker_url = env_broker
    celery_cfg = _get_celery_cfg()
    always_eager = env_bool(
        "CELERY_TASK_ALWAYS_EAGER",
        default=bool(celery_cfg.always_eager if celery_cfg else getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False)),
    )
    broker_mem = (broker_url or "").startswith(("memory://", "cache+memory://"))
    if not always_eager and not broker_mem:
        queue_names: list[str] | None = None
        if redis_cfg and redis_cfg.queue_names:
            queue_names = list(redis_cfg.queue_names)
        else:
            raw_queue_names = getattr(settings, "QUEUE_NAMES", None)
            if isinstance(raw_queue_names, str) and raw_queue_names.strip():
                queue_names = [item.strip() for item in raw_queue_names.split(",") if item.strip()]
        interval_s = int(
            celery_cfg.backlog_probe_seconds
            if celery_cfg
            else (redis_cfg.backlog_probe_seconds if redis_cfg else getattr(settings, "BACKLOG_PROBE_SECONDS", 15))
        )
        enable_celery_metrics(
            celery_app,
            broker_url=broker_url,
            queue_names=queue_names,
            backlog_interval_s=interval_s,
        )
        start_worker_metrics_http_if_enabled()

nested_celery_cfg = _get_celery_cfg()

if nested_celery_cfg is None:
    nested_celery_cfg = CelerySettings.from_settings(settings)

beat_entries: list[BeatScheduleEntry] = []

if nested_celery_cfg.schedule_nightly_maintenance:
    beat_entries.append(
        BeatScheduleEntry(
            "nightly-maintenance",
            task="ingest.maintenance_nightly",
            setting_name="NIGHTLY_MAINTENANCE_CRON",
            expression=str(nested_celery_cfg.nightly_maintenance_cron),
        )
    )

if nested_celery_cfg.schedule_mv_refresh:
    beat_entries.append(
        BeatScheduleEntry(
            "refresh-roi-fees-mvs",
            task="db.refresh_roi_mvs",
            setting_name="MV_REFRESH_CRON",
            expression=str(nested_celery_cfg.mv_refresh_cron),
        )
    )

if nested_celery_cfg.schedule_logistics_etl:
    beat_entries.append(
        BeatScheduleEntry(
            "logistics-etl-full",
            task="logistics.etl.full",
            setting_name="LOGISTICS_CRON",
            expression=str(nested_celery_cfg.logistics_cron),
        )
    )

beat_entries.append(
    BeatScheduleEntry(
        "alertbot-run",
        task="alertbot.run",
        setting_name="ALERTS_EVALUATION_INTERVAL_CRON",
        expression=str(nested_celery_cfg.alertbot_cron),
    )
)

validated_entries = _validate_cron_entries(beat_entries)
for name, task, schedule in validated_entries:
    _beat_schedule[name] = {
        "task": task,
        "schedule": schedule,
    }

alertbot_entry = _beat_schedule.get("alertbot-run")
if alertbot_entry:
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
