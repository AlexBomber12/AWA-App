from __future__ import annotations

import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy.orm import Session

from awa_common.db.load_log import (
    get_load_log_id,
    mark_failed,
    mark_success,
    soft_update_meta_on_duplicate,
    try_insert_load_log,
)
from awa_common.settings import settings as SETTINGS

SessionFactory = Callable[[], Session]


@dataclass
class ProcessHandle:
    session: Session
    load_log_id: int
    source: str
    idempotency_key: str
    task_id: str | None
    payload_meta: dict[str, Any]


@contextmanager
def process_once(
    session_factory: SessionFactory,
    *,
    source: str,
    payload_meta: dict[str, Any],
    idempotency_key: str,
    on_duplicate: Literal["skip", "update_meta"] = "skip",
    task_id: str | None = None,
    processed_by: str | None = None,
) -> Generator[ProcessHandle | None]:
    """Ensure the given source/payload is processed only once."""

    session = session_factory()
    processed_by = processed_by or SETTINGS.SERVICE_NAME
    try:
        result = try_insert_load_log(
            session,
            source=source,
            idempotency_key=idempotency_key,
            payload_meta=payload_meta,
            processed_by=processed_by,
            task_id=task_id,
        )

        if result == "duplicate":
            if on_duplicate == "update_meta":
                soft_update_meta_on_duplicate(
                    session,
                    source=source,
                    idempotency_key=idempotency_key,
                    payload_meta=payload_meta,
                    processed_by=processed_by,
                    task_id=task_id,
                )
                session.commit()
            else:
                session.rollback()
            yield None
            return

        session.commit()
        load_log_id = get_load_log_id(
            session,
            source=source,
            idempotency_key=idempotency_key,
        )
        if load_log_id is None:
            raise RuntimeError("Load log entry inserted but could not be retrieved.")

        handle = ProcessHandle(
            session=session,
            load_log_id=load_log_id,
            source=source,
            idempotency_key=idempotency_key,
            task_id=task_id,
            payload_meta=payload_meta,
        )
        started_at = time.perf_counter()

        try:
            yield handle
        except Exception as exc:
            session.rollback()
            mark_failed(session, load_log_id, str(exc))
            session.commit()
            raise
        else:
            duration_ms = int((time.perf_counter() - started_at) * 1000)
            mark_success(session, load_log_id, duration_ms)
            session.commit()
    finally:
        session.close()
