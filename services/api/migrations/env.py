from __future__ import annotations
from logging.config import fileConfig
from sqlalchemy import create_engine
from alembic import context  # type: ignore
import os
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from services.common.db_url import make_dsn


config = context.config
if config.config_file_name and os.path.exists(config.config_file_name):
    try:
        fileConfig(config.config_file_name)
    except Exception:
        pass

target_metadata = None


url = make_dsn(async_=False)
print("DSN:", url)
config.set_main_option("sqlalchemy.url", url)

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
