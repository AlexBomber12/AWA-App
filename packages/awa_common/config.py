from .dsn import build_dsn

ASYNC_DSN = build_dsn(sync=False)
SYNC_DSN = build_dsn(sync=True)

__all__ = ["ASYNC_DSN", "SYNC_DSN"]
