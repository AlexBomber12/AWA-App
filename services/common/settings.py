from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENABLE_LIVE: int = 1
    PG_USER: str = "postgres"
    PG_PASSWORD: str = "pass"
    PG_HOST: str = "localhost"
    PG_PORT: int = 5432
    PG_DATABASE: str = "awa"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def DATABASE_URL(self) -> str:
        if self.ENABLE_LIVE == 0:
            return "sqlite+aiosqlite:///data/awa.db"
        return f"postgresql+asyncpg://{self.PG_USER}:{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DATABASE}"


settings = Settings()
