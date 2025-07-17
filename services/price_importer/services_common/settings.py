from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENABLE_LIVE: int = 1
    PG_USER: str = "postgres"
    PG_PASSWORD: str = "pass"
    PG_HOST: str = "postgres"
    PG_PORT: int = 5432
    PG_DATABASE: str = "awa"
    DATA_DIR: Path = Path.cwd() / "data"

    model_config = SettingsConfigDict(env_file=".env.postgres", extra="ignore")

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.PG_USER}:{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DATABASE}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
