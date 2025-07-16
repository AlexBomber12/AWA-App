from pathlib import Path
from sqlalchemy import create_engine, text

from services.common.dsn import build_dsn
from services.returns_etl import loader
import pytest

pytestmark = pytest.mark.integration


def test_returns_loader(tmp_path, refresh_mvs):
    csv = Path("tests/fixtures/sample_returns.csv")
    loader.main([str(csv)])

    engine = create_engine(build_dsn(sync=True))
    with engine.connect() as conn:
        cnt = conn.execute(text("SELECT count(*) FROM returns_raw")).scalar()
    assert cnt == 2
