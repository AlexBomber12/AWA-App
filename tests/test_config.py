import os

from config import Settings, database_url


def test_database_url_default(monkeypatch) -> None:
    monkeypatch.setattr(Settings, "model_config", {"extra": "ignore"}, raising=False)
    os.environ.pop("DATABASE_URL", None)
    url = database_url()
    assert url.startswith("postgresql+asyncpg://")
