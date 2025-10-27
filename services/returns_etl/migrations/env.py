import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from awa_common.base import Base  # noqa: E402

config = context.config
if config.config_file_name and os.path.exists(config.config_file_name):
    try:
        fileConfig(config.config_file_name)
    except KeyError:
        pass

target_metadata = Base.metadata


def run_migrations_online() -> None:
    url = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://postgres:pass@localhost:5432/awa"
    ).replace("asyncpg", "psycopg")
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=url,
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


run_migrations_online()
