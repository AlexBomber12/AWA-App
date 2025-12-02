from __future__ import annotations

import sqlalchemy as sa
from alembic import op  # type: ignore[attr-defined]
from sqlalchemy.dialects import postgresql

revision = "7e66e1d1c4e9"
down_revision = "7d0fa0b0d8c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    _add_links_column()
    _backfill_links()
    _recreate_roi_index()
    _create_task_indexes()


def downgrade() -> None:
    _drop_task_indexes()
    _restore_roi_index()
    _drop_links_column()


def _connection():
    return op.get_bind()


def _context():
    return op.get_context()


def _run_concurrent(sql: str) -> None:
    with _context().autocommit_block():
        _connection().execute(sa.text(sql))


def _table_exists(schema: str, table: str) -> bool:
    stmt = sa.text(
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = :schema AND table_name = :table
        LIMIT 1
        """
    )
    result = _connection().execute(stmt, {"schema": schema, "table": table})
    return result.scalar() is not None


def _add_links_column() -> None:
    op.add_column(
        "tasks",
        sa.Column(
            "links",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )


def _backfill_links() -> None:
    op.execute(
        """
        UPDATE tasks
        SET links = jsonb_strip_nulls(
            COALESCE(links, '{}'::jsonb)
            || jsonb_build_object(
                'asin', asin,
                'vendor_id', vendor_id,
                'thread_id', thread_id,
                'entity_type', entity_type
            )
        )
        """
    )


def _drop_links_column() -> None:
    op.drop_column("tasks", "links")


def _recreate_roi_index() -> None:
    if not _table_exists("public", "mat_v_roi_full"):
        return
    _run_concurrent("DROP INDEX IF EXISTS ix_mat_v_roi_full_roi_pct_asin")
    _run_concurrent(
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_mat_v_roi_full_roi_pct_asin
        ON public.mat_v_roi_full USING btree (roi_pct DESC NULLS LAST, asin)
        """
    )
    _run_concurrent("ANALYZE public.mat_v_roi_full")


def _restore_roi_index() -> None:
    if not _table_exists("public", "mat_v_roi_full"):
        return
    _run_concurrent("DROP INDEX IF EXISTS ix_mat_v_roi_full_roi_pct_asin")
    _run_concurrent(
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_mat_v_roi_full_roi_pct_asin
        ON public.mat_v_roi_full USING btree (roi_pct DESC, asin)
        """
    )
    _run_concurrent("ANALYZE public.mat_v_roi_full")


def _create_task_indexes() -> None:
    _run_concurrent(
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_tasks_priority_deadline_created
        ON tasks (priority DESC, deadline_at ASC NULLS LAST, created_at DESC, id)
        """
    )
    _run_concurrent(
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_tasks_state_priority_deadline_created
        ON tasks (state, priority DESC, deadline_at ASC NULLS LAST, created_at DESC, id)
        """
    )


def _drop_task_indexes() -> None:
    _run_concurrent("DROP INDEX IF EXISTS ix_tasks_state_priority_deadline_created")
    _run_concurrent("DROP INDEX IF EXISTS ix_tasks_priority_deadline_created")
