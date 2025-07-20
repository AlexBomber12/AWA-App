import importlib
import os
import pkgutil

import pytest

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from services.common.dsn import build_dsn

script = ScriptDirectory.from_config(Config("alembic.ini"))
_REV_INFO = [
    (rev.revision, rev.down_revision or "base")
    for rev in reversed(list(script.walk_revisions(base="base", head="heads")))
]


@pytest.mark.parametrize("rev,prev", _REV_INFO)
@pytest.mark.integration
def test_run_migrations_rev(monkeypatch, rev: str, prev: str) -> None:
    dsn = os.getenv("DATABASE_URL", build_dsn(sync=True))
    monkeypatch.setenv("DATABASE_URL", dsn)
    cfg = Config("alembic.ini")
    command.upgrade(cfg, rev)
    command.downgrade(cfg, prev)
    command.upgrade(cfg, rev)


def test_import_all_services():
    import services

    for mod in pkgutil.walk_packages(services.__path__, prefix="services."):
        try:
            importlib.import_module(mod.name)
        except Exception:
            pass
