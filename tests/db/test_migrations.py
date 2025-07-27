import psycopg
import pytest
from sqlalchemy.exc import OperationalError

from alembic import command
from alembic.config import Config


def test_run_all_migrations() -> None:
    cfg = Config("services/api/alembic.ini")
    try:
        command.upgrade(cfg, "head")
        command.downgrade(cfg, "base")
    except (psycopg.OperationalError, OperationalError):
        pytest.skip("Postgres unreachable")
