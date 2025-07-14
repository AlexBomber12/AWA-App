from tests.conftest import *  # noqa

import os
import urllib.parse
import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic import command


@pytest.fixture(scope="session")
def pg_engine():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        host = os.getenv("PG_HOST", "localhost")
        port = os.getenv("PG_PORT", "5432")
        user = urllib.parse.quote_plus(os.getenv("PG_USER", "postgres"))
        pwd = urllib.parse.quote_plus(os.getenv("PG_PASSWORD", "pass"))
        db = os.getenv("PG_DATABASE", "awa")
        dsn = f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
    dsn = dsn.replace("postgresql+psycopg://", "postgresql://")
    engine = sa.create_engine(dsn, future=True)

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", dsn)
    command.upgrade(cfg, "head")

    yield engine
    engine.dispose()
