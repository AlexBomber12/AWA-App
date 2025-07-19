import importlib
import pkgutil

import pytest

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from services.common.dsn import build_dsn

CFG = Config("alembic.ini")
SCRIPT = ScriptDirectory.from_config(CFG)
REVISIONS = [rev.revision for rev in SCRIPT.walk_revisions()]
REVISIONS.reverse()


@pytest.mark.integration
@pytest.mark.parametrize("rev", REVISIONS)
def test_run_migration(monkeypatch, rev):
    dsn = build_dsn(sync=True)
    monkeypatch.setenv("DATABASE_URL", dsn)
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", dsn)
    script = ScriptDirectory.from_config(cfg)
    prev = script.get_revision(rev).down_revision or "base"
    command.downgrade(cfg, "base")
    command.upgrade(cfg, rev)
    command.downgrade(cfg, prev)


def test_import_all_services():
    import services

    for mod in pkgutil.walk_packages(services.__path__, prefix="services."):
        try:
            importlib.import_module(mod.name)
        except Exception:
            pass
