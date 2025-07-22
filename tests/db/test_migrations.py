import os
import subprocess

import pytest
import sqlalchemy as sa

from services.common.dsn import build_dsn


@pytest.mark.integration
def test_alembic_upgrade_head() -> None:
    url = build_dsn(sync=True)
    env = os.environ.copy()
    env["DATABASE_URL"] = url
    subprocess.check_call(["alembic", "upgrade", "head"], env=env)
    eng = sa.create_engine(url)
    insp = sa.inspect(eng)
    assert "products" in insp.get_table_names()
