import subprocess
import os
from sqlalchemy import create_engine, text
from services.common.db_url import build_url


def test_upgrade_storage_fee_column_exists(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ENABLE_LIVE", "0")
    env = {**os.environ, "DATA_DIR": str(tmp_path), "ENABLE_LIVE": "0"}
    db_path = tmp_path / "awa.db"
    if db_path.exists():
        db_path.unlink()
    subprocess.run(["alembic", "upgrade", "head"], check=True, env=env)
    engine = create_engine(build_url(async_=False))
    with engine.connect() as conn:
        conn.execute(text("SELECT storage_fee FROM fees_raw LIMIT 1"))
