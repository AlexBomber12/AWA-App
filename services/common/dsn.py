import os
import urllib.parse as _u


def build_dsn() -> str:
    if url := os.getenv("DATABASE_URL"):
        return url
    host = os.getenv("PG_HOST", "localhost")
    port = os.getenv("PG_PORT", "5432")
    user = _u.quote_plus(os.getenv("PG_USER", "postgres"))
    pwd = _u.quote_plus(os.getenv("PG_PASSWORD", "pass"))
    db = os.getenv("PG_DATABASE", "awa")
    return f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
