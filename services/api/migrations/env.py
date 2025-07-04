from __future__ import annotations
from logging.config import fileConfig
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from alembic import context  # type: ignore
import os
import time


config = context.config
if config.config_file_name and os.path.exists(config.config_file_name):
    try:
        fileConfig(config.config_file_name)
    except Exception:
        pass

target_metadata = None


url = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:pass@postgres:5432/postgres",
)

# Migrations run synchronously. If the provided DATABASE_URL uses an async driver
# like ``asyncpg``, convert it to the equivalent synchronous ``psycopg`` driver
# so Alembic can connect without greenlets.
url_obj = make_url(url)
if url_obj.drivername.endswith("asyncpg"):
    url_obj = url_obj.set(drivername=url_obj.drivername.replace("asyncpg", "psycopg"))
url = str(url_obj)

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
    for attempt in range(10):
        try:
            with connectable.connect() as connection:
                context.configure(
                    connection=connection, target_metadata=target_metadata
                )
                with context.begin_transaction():
                    context.run_migrations()
            break
        except Exception:
            if attempt == 9:
                raise
            time.sleep(0.5)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
