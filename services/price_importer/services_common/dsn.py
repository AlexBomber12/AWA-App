import os
import urllib.parse as _u


def build_dsn(sync: bool = True) -> str:
    """Return safe DSN.

    Prefers explicit DSNs via ``PG_SYNC_DSN``/``PG_ASYNC_DSN`` or ``DATABASE_URL``.
    Falls back to individual PG_* variables.
    sync=True → SQLAlchemy (+psycopg) else plain asyncpg.
    """

    url = os.getenv("PG_SYNC_DSN" if sync else "PG_ASYNC_DSN")
    if url:
        return url.replace(
            "postgresql://",
            "postgresql+psycopg://" if sync else "postgresql+asyncpg://",
        )
    if not url:
        other = os.getenv("PG_ASYNC_DSN" if sync else "PG_SYNC_DSN")
        if other:
            if sync:
                return other.replace("+asyncpg", "+psycopg").replace(
                    "postgresql://", "postgresql+psycopg://"
                )
            return other.replace("+psycopg", "+asyncpg").replace(
                "postgresql://", "postgresql+asyncpg://"
            )

    url = os.getenv("DATABASE_URL")
    if url:
        if "+asyncpg" in url or "+psycopg" in url:
            return (
                url.replace("+asyncpg", "+psycopg") if sync else url.replace("+psycopg", "+asyncpg")
            )
        return url.replace(
            "postgresql://",
            "postgresql+psycopg://" if sync else "postgresql+asyncpg://",
        )

    host = os.getenv("PG_HOST", "localhost")
    port = os.getenv("PG_PORT", "5432")
    user = _u.quote_plus(os.getenv("PG_USER", "postgres"))
    pwd = _u.quote_plus(os.getenv("PG_PASSWORD", "pass"))
    db = os.getenv("PG_DATABASE", "awa")
    base = f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
    if sync:
        return base.replace("postgresql://", "postgresql+psycopg://")
    return base.replace("postgresql://", "postgresql+asyncpg://")


__all__ = ["build_dsn"]
