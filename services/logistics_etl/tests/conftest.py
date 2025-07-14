from tests.conftest import *  # noqa

import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic import command  # type: ignore[attr-defined]
from services.common.dsn import build_dsn

pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def pg_engine():
    dsn = build_dsn(sync=True)
    engine = sa.create_engine(dsn, future=True)

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", dsn)
    command.upgrade(cfg, "head")

    yield engine
    engine.dispose()
