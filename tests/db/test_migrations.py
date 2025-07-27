from alembic.config import Config
from alembic import command


def test_upgrade_head():
    cfg = Config("services/api/alembic.ini")
    command.upgrade(cfg, "head")
