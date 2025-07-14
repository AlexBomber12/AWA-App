import os


def make_dsn(async_: bool = False) -> str:
    """Return DSN built from either PG_* or POSTGRES_* vars."""
    user = os.getenv("PG_USER") or os.getenv("POSTGRES_USER", "postgres")
    pwd = os.getenv("PG_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "")
    host = os.getenv("PG_HOST") or os.getenv("POSTGRES_HOST", "localhost")
    db = os.getenv("PG_DATABASE") or os.getenv("POSTGRES_DB", "postgres")
    scheme = "postgresql+asyncpg" if async_ else "postgresql+psycopg"
    return f"{scheme}://{user}:{pwd}@{host}:5432/{db}"


def build_url(async_: bool = False) -> str:
    """Return Postgres DSN built from environment variables."""
    return make_dsn(async_)
