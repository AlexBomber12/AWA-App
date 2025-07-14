from sqlalchemy import create_engine, text
from alembic.config import Config  # type: ignore[attr-defined]
from alembic import command  # type: ignore[attr-defined]
from services.common.dsn import build_dsn


def test_upgrade_storage_fee_column_exists(tmp_path, monkeypatch, pg_pool):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ENABLE_LIVE", "0")
    db_path = tmp_path / "awa.db"
    if db_path.exists():
        db_path.unlink()
    if db_path.exists():
        db_path.unlink(missing_ok=True)
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    command.upgrade(cfg, "head")
    engine = create_engine(build_dsn())
    with engine.connect() as conn:
        conn.execute(text("SELECT storage_fee FROM fees_raw LIMIT 1"))
