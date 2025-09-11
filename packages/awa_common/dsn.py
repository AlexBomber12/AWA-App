import os
import urllib.parse as _u


def build_dsn(sync: bool = True) -> str:
    """Return a Postgres DSN, validating required variables.

    The function prefers explicit DSNs via ``PG_SYNC_DSN`` / ``PG_ASYNC_DSN`` or
    ``DATABASE_URL``.  If those are absent it assembles a connection string from
    ``PG_HOST`` and related variables and raises a helpful error when any are
    missing.
    """

    def _apply_host_override(u: str) -> str:
        """If PG_HOST is set, force the DSN host to match it.

        This makes DSN values portable between Docker (host 'postgres') and CI/
        local runs (host 'localhost'). If the DSN already matches PG_HOST, it is
        left unchanged. When overriding, prefer PG_PORT if set, otherwise keep
        the port from the DSN.
        """
        host = os.getenv("PG_HOST") or os.getenv("PGHOST")
        port = os.getenv("PG_PORT") or os.getenv("PGPORT")
        if not host:
            return u

        parsed = _u.urlparse(u)
        # Only override when the DSN has a hostname and it differs from PG_HOST
        if parsed.hostname and parsed.hostname != host:
            auth = ""
            if parsed.username:
                auth = parsed.username
                if parsed.password:
                    auth += f":{parsed.password}"
                auth += "@"
            effective_port = port or (str(parsed.port) if parsed.port else "")
            netloc = f"{auth}{host}{":" + effective_port if effective_port else ''}"
            u = parsed._replace(netloc=netloc).geturl()
        return u

    url = os.getenv("PG_SYNC_DSN" if sync else "PG_ASYNC_DSN")
    if url:
        url = _apply_host_override(url)
        return url.replace(
            "postgresql://",
            "postgresql+psycopg://" if sync else "postgresql+asyncpg://",
        )
    if not url:
        other = os.getenv("PG_ASYNC_DSN" if sync else "PG_SYNC_DSN")
        if other:
            other = _apply_host_override(other)
            if sync:
                return other.replace("+asyncpg", "+psycopg").replace(
                    "postgresql://", "postgresql+psycopg://"
                )
            return other.replace("+psycopg", "+asyncpg").replace(
                "postgresql://", "postgresql+asyncpg://"
            )

    url = os.getenv("DATABASE_URL")
    if url:
        url = _apply_host_override(url)
        if "+asyncpg" in url or "+psycopg" in url:
            return (
                url.replace("+asyncpg", "+psycopg")
                if sync
                else url.replace("+psycopg", "+asyncpg")
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
