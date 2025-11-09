from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import structlog
from celery import states

from awa_common.metrics import instrument_task as _instrument_task
from services.alert_bot import worker as alerts_worker
from services.worker.celery_app import celery_app


def _fallback_async_to_sync(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.run(func(*args, **kwargs))

    return wrapper


try:  # pragma: no cover - fallback when asgiref is missing
    from asgiref.sync import async_to_sync as _async_to_sync
except ModuleNotFoundError:  # pragma: no cover - allows tests without asgiref
    _async_to_sync = _fallback_async_to_sync


async_to_sync: Callable[..., Any] = cast(Callable[..., Any], _async_to_sync)

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Protocol, TypeVar

    _InstrumentFunc = TypeVar("_InstrumentFunc", bound=Callable[..., Any])

    class _InstrumentTaskCallable(Protocol):
        def __call__(
            self, task_name: str, *, emit_metrics: bool = True
        ) -> Callable[[_InstrumentFunc], _InstrumentFunc]: ...

    instrument_task: _InstrumentTaskCallable = _instrument_task
else:
    instrument_task = _instrument_task

logger = structlog.get_logger(__name__)
_evaluate_alerts_sync: Callable[[], dict[str, int]] = async_to_sync(alerts_worker.evaluate_alert_rules)


def _download_minio_to_tmp(uri: str) -> Path:
    from urllib.parse import urlparse

    from minio import Minio

    parsed = urlparse(uri)
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    secure = os.getenv("MINIO_SECURE", "false").lower() in ("1", "true", "yes")
    access_key = os.getenv("MINIO_ACCESS_KEY")
    secret_key = os.getenv("MINIO_SECRET_KEY")
    client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
    tmpdir = Path(tempfile.mkdtemp(prefix="ingest_"))
    dst = tmpdir / Path(key).name
    client.fget_object(bucket, key, str(dst))
    return dst


def _resolve_uri_to_path(uri: str) -> Path:
    if uri.startswith("minio://"):
        return _download_minio_to_tmp(uri)
    if uri.startswith("file://"):
        return Path(uri[len("file://") :])
    return Path(uri)


@celery_app.task(name="ingest.import_file", bind=True)  # type: ignore[misc]
@instrument_task("ingest.import_file", emit_metrics=False)
def task_import_file(self: Any, uri: str, report_type: str | None = None, force: bool = False) -> dict[str, Any]:
    """Import a file into Postgres using existing ETL pipeline."""

    self.update_state(state=states.STARTED, meta={"stage": "resolve_uri"})
    tmp_dir: Path | None = None
    try:
        local_path = _resolve_uri_to_path(uri)
        if "ingest_" in str(local_path.parent):
            tmp_dir = local_path.parent

        from etl.load_csv import import_file as run_ingest

        self.update_state(state=states.STARTED, meta={"stage": "ingest"})
        result = run_ingest(
            str(local_path),
            report_type=report_type,
            celery_update=lambda m: self.update_state(state=states.STARTED, meta=m),
            force=force,
        )
        summary: dict[str, Any] = {}
        if isinstance(result, dict):
            summary.update(result)
        summary.setdefault("status", "success")
        self.update_state(state=states.SUCCESS, meta=summary)
        return summary
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("task_import_file failed for %s", uri)
        meta = {"status": "error", "error": str(exc)}
        self.update_state(state=states.FAILURE, meta=meta)
        raise
    finally:
        if tmp_dir and tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)


@celery_app.task(name="ingest.rebuild_views", bind=True)  # type: ignore[misc]
@instrument_task("ingest.rebuild_views", emit_metrics=False)
def task_rebuild_views(self: Any) -> dict[str, Any]:
    logger.info("rebuild_views.noop")
    return {"status": "success", "message": "noop"}


if os.getenv("TESTING") == "1":

    @celery_app.task(name="ingest.enqueue_import", bind=True)  # type: ignore[misc]
    def enqueue_import(self: Any, *, uri: str, dialect: str) -> dict[str, Any]:  # pragma: no cover - helper for tests
        from etl.load_csv import import_file as run_ingest

        return run_ingest(uri, dialect=dialect)


@celery_app.task(name="alerts.evaluate_rules")  # type: ignore[misc]
@instrument_task("alerts.evaluate_rules")
def evaluate_alert_rules() -> dict[str, int]:
    """Periodic task that evaluates configured alert rules."""

    return _evaluate_alerts_sync()


@celery_app.task(name="alerts.rules_health")  # type: ignore[misc]
@instrument_task("alerts.rules_health")
def alert_rules_health() -> dict[str, Any]:
    """Periodic task that refreshes Telegram availability state."""

    return alerts_worker.alert_rules_health()
