from __future__ import annotations

from alembic import op


def replace_view(name: str, new_sql: str) -> None:
    """Drop and recreate a SQL view atomically."""
    op.execute(f"DROP VIEW IF EXISTS {name} CASCADE;")
    op.execute(new_sql)
