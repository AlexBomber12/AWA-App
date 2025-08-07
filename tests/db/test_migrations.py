from alembic import command
from alembic.config import Config


def test_upgrade_head():
    cfg = Config("services/api/alembic.ini")
    command.upgrade(cfg, "head")
