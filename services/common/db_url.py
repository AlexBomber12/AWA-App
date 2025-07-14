import os


def build_url(async_: bool = False) -> str:
    """Return Postgres DSN built from `DATABASE_URL`."""
    url = os.environ["DATABASE_URL"]
    if async_:
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://")
        return url
    return url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
