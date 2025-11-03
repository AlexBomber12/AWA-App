"""Local DSN builder to avoid cross-service dependency."""

from __future__ import annotations

import os
import urllib.parse as _u


def build_dsn(sync: bool = True) -> str:
    """Return a Postgres DSN assembled from environment variables.

    Prefers explicit DSNs via ``PG_SYNC_DSN``/``PG_ASYNC_DSN`` or
    ``DATABASE_URL``. Falls back to individual PG_* settings and raises an
    error when any required variable is missing.
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

    required = ["PG_USER", "PG_PASSWORD", "PG_DATABASE", "PG_HOST", "PG_PORT"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Missing required env vars: {joined}")

    user = _u.quote_plus(os.getenv("PG_USER") or "")
    pwd = _u.quote_plus(os.getenv("PG_PASSWORD") or "")
    host = os.getenv("PG_HOST")
    port = os.getenv("PG_PORT")
    db = os.getenv("PG_DATABASE")
    base = f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
    if sync:
        return base.replace("postgresql://", "postgresql+psycopg://")
    return base.replace("postgresql://", "postgresql+asyncpg://")


__all__ = ["build_dsn"]
