from __future__ import annotations

from alembic import op


def quote_ident(identifier: str) -> str:
    """
    Return a quoted SQL identifier, handling dotted schema-qualified names.

    Raises ValueError when the identifier is empty or contains invalid segments.
    """
    if not isinstance(identifier, str):
        raise TypeError("identifier must be a string")
    parts = [part.strip() for part in identifier.split(".")]
    if not parts or any(not part for part in parts):
        raise ValueError("identifier must contain non-empty segments")
    quoted_parts = []
    for part in parts:
        escaped = part.replace('"', '""')
        quoted_parts.append(f'"{escaped}"')
    return ".".join(quoted_parts)


def render_drop_view(name: str, *, cascade: bool = True) -> str:
    suffix = " CASCADE" if cascade else ""
    return f"DROP VIEW IF EXISTS {quote_ident(name)}{suffix};"


def render_create_view(name: str, body_sql: str, *, replace: bool = True) -> str:
    statement = "CREATE OR REPLACE VIEW" if replace else "CREATE VIEW"
    return f"{statement} {quote_ident(name)} AS\n{body_sql.strip()}"


def replace_view(name: str, new_sql: str) -> None:
    """Drop and recreate a SQL view atomically."""
    op.execute(render_drop_view(name))
    op.execute(new_sql.strip())


__all__ = ["quote_ident", "render_drop_view", "render_create_view", "replace_view"]
