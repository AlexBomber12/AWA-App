from awa_common.dsn import build_dsn


def pg_dsn() -> str:
    """Return Postgres DSN for CLI scripts."""
    return build_dsn()
