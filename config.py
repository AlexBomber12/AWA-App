import os


def database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    if user and password and db:
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
    return "sqlite+aiosqlite:///data/awa.db"
