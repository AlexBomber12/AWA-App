import os
import urllib.parse as _u


def build_dsn(sync: bool = True) -> str:
    """Return safe DSN.

    sync=True → SQLAlchemy (+psycopg) else plain asyncpg.
    """

    url = os.getenv("DATABASE_URL")
    if url:
        return url if sync else url.replace("+psycopg", "")

    host = os.getenv("PG_HOST", "localhost")
    port = os.getenv("PG_PORT", "5432")
    user = _u.quote_plus(os.getenv("PG_USER", "postgres"))
    pwd = _u.quote_plus(os.getenv("PG_PASSWORD", "pass"))
    db = os.getenv("PG_DATABASE", "awa")
    base = f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
    return base if not sync else base.replace("postgresql://", "postgresql+psycopg://")
