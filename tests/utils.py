from pathlib import Path

from alembic import command  # type: ignore[attr-defined]
from alembic.config import Config


async def run_migrations() -> None:
    cfg = Config("alembic.ini")
    # ensure script_location resolves correctly when tests run from any CWD
    cfg.set_main_option("script_location", str(Path("services/api/migrations")))
    command.upgrade(cfg, "head")
