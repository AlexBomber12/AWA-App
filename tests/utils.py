from alembic.config import Config
from alembic import command
from pathlib import Path


async def run_migrations() -> None:
    cfg = Config("alembic.ini")
    # ensure script_location resolves correctly when tests run from any CWD
    cfg.set_main_option("script_location", str(Path("services/api/migrations")))
    command.upgrade(cfg, "head")
