from tests.conftest import *  # noqa

import os
import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic import command


@pytest.fixture(scope="session")
def pg_engine():
    url = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")
    engine = sa.create_engine(url, future=True)

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    yield engine
    engine.dispose()
