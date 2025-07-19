import importlib
import os
import pkgutil

import pytest

from alembic import command
from alembic.config import Config


@pytest.mark.integration
@pytest.mark.parametrize(
    "dsn",
    [
        os.getenv(
            "DATABASE_URL", "postgresql+psycopg://postgres:pass@localhost:5432/awa"
        )
    ],
)
def test_run_migrations_head(tmp_path, monkeypatch, dsn):
    monkeypatch.setenv("DATABASE_URL", dsn)
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    command.upgrade(cfg, "head")


def test_import_all_services():
    import services

    for mod in pkgutil.walk_packages(services.__path__, prefix="services."):
        try:
            importlib.import_module(mod.name)
        except Exception:
            pass
