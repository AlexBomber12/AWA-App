from tests.conftest import *  # noqa

import pytest
import sqlalchemy as sa
from alembic.config import CommandLine, Config


@pytest.fixture
def pg_engine(postgresql_proc):
    url = (
        f"postgresql://{postgresql_proc.user}:{postgresql_proc.password or ''}"
        f"@{postgresql_proc.host}:{postgresql_proc.port}/{postgresql_proc.dbname}"
    )
    engine = sa.create_engine(url, future=True)

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    CommandLine().run_cmd(cfg, ["upgrade", "head"])

    yield engine
    engine.dispose()
