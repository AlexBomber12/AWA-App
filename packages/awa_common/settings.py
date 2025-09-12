from pydantic_settings import BaseSettings
from pydantic import AnyUrl


class Settings(BaseSettings):
    APP_NAME: str = "awa-app"
    ENV: str = "local"
    DATABASE_URL: str | None = None  # e.g. postgresql+psycopg://user:pass@db:5432/app
    REDIS_URL: str = "redis://redis:6379/0"
    SENTRY_DSN: str | None = None

    class Config:
        env_file = ".env.local"


settings = Settings()
