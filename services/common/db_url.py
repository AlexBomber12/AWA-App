import os


def build_url(async_: bool = True) -> str:
    """Return Postgres DSN built from env vars without assuming `DATABASE_URL`."""
    url = os.getenv("DATABASE_URL")
    if url:
        if async_ and url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://")
        if not async_ and url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql://")
        return url

    user = os.getenv("PG_USER", "postgres")
    password = os.getenv("PG_PASSWORD", "pass")
    host = os.getenv("PG_HOST", "localhost")
    port = os.getenv("PG_PORT", "5432")
    database = os.getenv("PG_DATABASE", "awa")
    scheme = "postgresql+asyncpg" if async_ else "postgresql"
    return f"{scheme}://{user}:{password}@{host}:{port}/{database}"
