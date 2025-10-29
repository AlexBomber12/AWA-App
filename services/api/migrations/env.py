from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from awa_common.base import Base
from awa_common.settings import settings
from sqlalchemy import create_engine, pool

from services.db.utils import views as view_helpers

# Alembic config is only available when invoked by the CLI.
try:
    config = context.config
except Exception:  # pragma: no cover - guard for imports outside Alembic
    config = None

if config and config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    """Return the canonical sync database URL for migrations."""
    env_override = (os.getenv("DATABASE_URL") or "").strip()
    if env_override:
        return env_override
    url = getattr(settings, "DATABASE_URL", None)
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")
    return str(url)


def run_migrations_offline() -> None:
    url = _database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = _database_url()
    connectable = create_engine(url, poolclass=pool.NullPool)
    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                compare_server_default=True,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


if config:
    config.set_main_option("script_location", "services/api/migrations")
    config.set_main_option("sqlalchemy.url", _database_url())
    config.attributes["view_helpers"] = view_helpers
    config.attributes["replace_view"] = view_helpers.replace_view

    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
