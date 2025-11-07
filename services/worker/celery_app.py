from __future__ import annotations

import importlib
import json
import logging
import os

from celery import Celery
from celery.schedules import crontab

from awa_common.logging import configure_logging
from awa_common.metrics import enable_celery_metrics, init as metrics_init, start_worker_metrics_http_if_enabled
from awa_common.settings import settings

_worker_version = getattr(settings, "APP_VERSION", "0.0.0")

configure_logging(service="worker", env=settings.ENV, version=_worker_version)
metrics_init(service="worker", env=settings.ENV, version=_worker_version)
logging.getLogger(__name__).info("settings=%s", json.dumps(settings.redacted()))


def _init_sentry() -> None:
    dsn = (settings.SENTRY_DSN or "").strip()
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.celery import CeleryIntegration
    except Exception:  # pragma: no cover - optional telemetry
        return
    BadDsnT: type[BaseException]
    try:
        from sentry_sdk.utils import BadDsn as _BadDsn
    except Exception:  # pragma: no cover
        BadDsnT = Exception
    else:
        BadDsnT = _BadDsn
    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=settings.ENV,
            release=os.getenv("SENTRY_RELEASE") or os.getenv("COMMIT_SHA"),
            send_default_pii=False,
            integrations=[CeleryIntegration()],
        )
    except BadDsnT:
        logging.getLogger(__name__).warning("Ignoring invalid SENTRY_DSN", exc_info=False)
    except Exception:
        logging.getLogger(__name__).debug("Sentry init failed – continuing without telemetry", exc_info=True)


_init_sentry()


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

if os.getenv("SCHEDULE_MV_REFRESH", "true").lower() in ("1", "true", "yes"):
    cron_expr = os.getenv("MV_REFRESH_CRON", "*/15 * * * *")
    mv_cron = cron_expr.split()
    if len(mv_cron) != 5:
        mv_cron = "*/15 * * * *".split()
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
