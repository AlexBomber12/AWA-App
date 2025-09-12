from .dsn import build_dsn


def build_url(async_: bool = True) -> str:
    """Return Postgres DSN from environment variables."""
    return build_dsn(sync=not async_)


__all__ = ["build_url"]
