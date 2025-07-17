from pathlib import Path

from alembic import command  # type: ignore[attr-defined]
from alembic.config import Config


async def run_migrations() -> None:
    cfg = Config("alembic.ini")
    # ensure script_location resolves correctly when tests run from any CWD
    cfg.set_main_option("script_location", str(Path("services/api/migrations")))
    command.upgrade(cfg, "head")


def test_import_all_services() -> None:
    """Ensure all service packages can be imported."""
    import pkgutil

    for mod in pkgutil.walk_packages(["services"], prefix="services."):
        __import__(mod.name)
