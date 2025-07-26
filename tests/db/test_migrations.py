import os
import pathlib
import subprocess

import pytest
from sqlalchemy.exc import OperationalError

from alembic.command import upgrade
from alembic.config import Config


def test_all_migrations_apply() -> None:
    host = os.getenv("PG_HOST", "localhost")
    port = os.getenv("PG_PORT", "5432")
    script = pathlib.Path("services/etl/wait-for-it.sh")
    subprocess.run(["bash", str(script), f"{host}:{port}", "-t", "30"], check=True)
    cfg = Config("services/api/alembic.ini")
    try:
        upgrade(cfg, "head")
    except OperationalError:
        pytest.skip("Postgres unreachable")
