from alembic.config import Config
from alembic import command


async def run_migrations() -> None:
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
