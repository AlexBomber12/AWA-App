import os
import shutil
from decimal import Decimal

import pytest
import sqlalchemy as sa

from alembic import command
from alembic.config import Config


@pytest.fixture(scope="session", autouse=True)
def _migrate():
    """Override migrate fixture from conftest."""
    yield


@pytest.mark.skipif(shutil.which("initdb") is None, reason="initdb not available")
def test_refund_view_type_and_values():
    testing = pytest.importorskip("testing.postgresql")
    with testing.Postgresql() as pg:
        os.environ["DATABASE_URL"] = pg.url().replace("postgresql://", "postgresql+psycopg://")
        cfg = Config("alembic.ini")
        command.upgrade(cfg, "head")

        engine = sa.create_engine(os.environ["DATABASE_URL"])
        with engine.begin() as conn:
            conn.execute(
                sa.text(
                    "INSERT INTO refunds_raw (asin, amount, created_at) VALUES ('SKU1', 1.23, now())"
                )
            )
            refunds = conn.execute(sa.text("SELECT refunds FROM v_refund_totals WHERE asin='SKU1'"))
            val = refunds.scalar()
            dtype = conn.execute(
                sa.text(
                    """
                    SELECT data_type FROM information_schema.columns
                     WHERE table_name='v_refund_totals' AND column_name='refunds'
                    """
                )
            ).scalar()
        assert dtype == "numeric"
        assert val == Decimal("1.23")
