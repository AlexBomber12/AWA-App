from __future__ import annotations
from logging.config import fileConfig
from sqlalchemy import create_engine
from alembic import context  # type: ignore
import os


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None


url = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:pass@postgres:5432/postgres",
)
connectable = create_engine(url, pool_pre_ping=True)


def run_migrations_offline() -> None:
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
