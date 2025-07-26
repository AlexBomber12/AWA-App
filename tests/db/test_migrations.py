from alembic.command import upgrade
from alembic.config import Config


def test_all_migrations_apply() -> None:
    cfg = Config("services/api/alembic.ini")
    upgrade(cfg, "head")
