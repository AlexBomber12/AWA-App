from __future__ import annotations

from typing import Literal

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    func,
    select,
    text,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB, insert as pg_insert
from sqlalchemy.orm import Session

metadata = MetaData()

LOAD_LOG = Table(
    "load_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source", String(128), nullable=False),
    Column("idempotency_key", String(64), nullable=False),
    Column("status", String(16), nullable=False),
    Column("payload_meta", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column("processed_by", String(64)),
    Column("task_id", String(64)),
    Column("duration_ms", Integer),
    Column("error_message", Text),
    Column("created_at", DateTime(timezone=True), server_default=text("now()")),
    Column("updated_at", DateTime(timezone=True), server_default=text("now()")),
)

STATUS_PENDING = "pending"
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"


def try_insert_load_log(
    session: Session,
    *,
    source: str,
    idempotency_key: str,
    payload_meta: dict | None,
    processed_by: str | None,
    task_id: str | None,
) -> Literal["inserted", "duplicate"]:
    payload = payload_meta or {}
    stmt = (
        pg_insert(LOAD_LOG)
        .values(
            source=source,
            idempotency_key=idempotency_key,
            status=STATUS_PENDING,
            payload_meta=payload,
            processed_by=processed_by,
            task_id=task_id,
        )
        .on_conflict_do_nothing(index_elements=[LOAD_LOG.c.source, LOAD_LOG.c.idempotency_key])
        .returning(LOAD_LOG.c.id)
    )
    inserted_id = session.execute(stmt).scalar_one_or_none()
    if inserted_id is None:
        return "duplicate"
    session.flush()
    return "inserted"


def mark_success(session: Session, load_log_id: int, duration_ms: int | None) -> None:
    values: dict = {
        "status": STATUS_SUCCESS,
        "updated_at": func.now(),
    }
    if duration_ms is not None:
        values["duration_ms"] = duration_ms
    session.execute(update(LOAD_LOG).where(LOAD_LOG.c.id == load_log_id).values(**values))


def mark_failed(session: Session, load_log_id: int, error_message: str) -> None:
    session.execute(
        update(LOAD_LOG)
        .where(LOAD_LOG.c.id == load_log_id)
        .values(
            status=STATUS_FAILED,
            error_message=error_message[:1024],
            updated_at=func.now(),
        )
    )


def soft_update_meta_on_duplicate(
    session: Session,
    *,
    source: str,
    idempotency_key: str,
    payload_meta: dict,
    processed_by: str | None = None,
    task_id: str | None = None,
) -> None:
    session.execute(
        update(LOAD_LOG)
        .where(
            LOAD_LOG.c.source == source,
            LOAD_LOG.c.idempotency_key == idempotency_key,
        )
        .values(
            payload_meta=payload_meta,
            processed_by=processed_by,
            task_id=task_id,
            status=STATUS_SKIPPED,
            updated_at=func.now(),
        )
    )


def get_load_log_id(session: Session, *, source: str, idempotency_key: str) -> int | None:
    stmt = (
        select(LOAD_LOG.c.id)
        .where(
            LOAD_LOG.c.source == source,
            LOAD_LOG.c.idempotency_key == idempotency_key,
        )
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()
