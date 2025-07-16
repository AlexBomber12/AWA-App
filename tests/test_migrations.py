import os

import pytest
from alembic import command
from alembic.config import Config


def test_all_migrations_reversible():
    testing = pytest.importorskip("testing.postgresql")
    with testing.Postgresql() as pg:
        os.environ["DATABASE_URL"] = pg.url().replace("postgresql://", "postgresql+psycopg://")
        cfg = Config("alembic.ini")
        command.upgrade(cfg, "head")
        command.downgrade(cfg, "base")
