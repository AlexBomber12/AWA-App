import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from services.common.base import Base  # noqa: E402
from services.common.dsn import build_dsn  # noqa: E402

# Guard against importing this module outside of Alembic context
try:
    config = context.config
except AttributeError:
    # This module is being imported outside of Alembic context (e.g., during testing)
    # Create a dummy config or exit early
    config = None

if config and config.config_file_name and os.path.exists(config.config_file_name):
    try:
        fileConfig(config.config_file_name)
    except KeyError:
        pass

target_metadata = Base.metadata


def run_migrations_online() -> None:
    if not config:
        return  # Exit early if not in Alembic context

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=build_dsn(sync=True),
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if config:  # Only run migrations if we have a proper Alembic context
    run_migrations_online()
