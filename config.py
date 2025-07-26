from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    enable_live: int = 0
    database_url: str | None = None
    postgres_user: str = "root"
    postgres_password: str = "pass"
    postgres_db: str = "awa"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    data_dir: Path = Path.cwd() / "data"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def dsn(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def database_url() -> str:
    return get_settings().dsn
