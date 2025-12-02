from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

import structlog

from awa_common.metrics import instrument_task as _instrument_task
from services.worker.celery_app import celery_app

logger = structlog.get_logger(__name__).bind(component="logistics_etl")

if TYPE_CHECKING:
    from typing import Protocol

    P = ParamSpec("P")
    R = TypeVar("R", covariant=True)
    _InstrumentFunc = TypeVar("_InstrumentFunc", bound=Callable[..., Any])

    class _InstrumentTaskCallable(Protocol):
        def __call__(
            self, task_name: str, *, emit_metrics: bool = True
        ) -> Callable[[_InstrumentFunc], _InstrumentFunc]: ...

    class _CeleryTask(Protocol[P, R]):
        def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...
        def apply_async(self, *args: Any, **kwargs: Any) -> Any: ...
        def delay(self, *args: P.args, **kwargs: P.kwargs) -> Any: ...

    def celery_task(*args: Any, **kwargs: Any) -> Callable[[Callable[P, R]], _CeleryTask[P, R]]: ...

    instrument_task: _InstrumentTaskCallable = _instrument_task
else:
    instrument_task = _instrument_task
    celery_task = celery_app.task


def _run_full_sync(dry_run: bool = False) -> list[dict[str, Any]]:
    from . import flow

    return flow.run_once_with_guard(dry_run=dry_run)


@celery_task(name="logistics.etl.full")
@instrument_task("logistics_etl", emit_metrics=False)
def logistics_etl_full() -> list[dict[str, Any]]:
    """Celery task entrypoint triggered by beat."""
    try:
        return _run_full_sync(dry_run=False)
    except Exception:  # pragma: no cover - let Celery handle retry/logging
        logger.exception("logistics_etl.task_failed")
        raise


def start() -> None:
    """Manual entrypoint used by __main__ for ad-hoc runs."""
    _run_full_sync(dry_run=False)
