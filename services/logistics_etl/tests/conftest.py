import pytest

pytest.importorskip("asyncpg")
pytest.importorskip("sqlalchemy")

import sqlalchemy as sa  # noqa: E402

from alembic import command  # type: ignore[attr-defined]  # noqa: E402
from alembic.config import Config  # noqa: E402
from services.common.dsn import build_dsn  # noqa: E402
from tests.conftest import *  # noqa: E402,F403

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
