from services.price_importer.services_common.dsn import build_dsn


def make_dsn(async_: bool = False) -> str:
    """Return DSN using shared builder."""
    return build_dsn(sync=not async_)


def build_url(async_: bool = False) -> str:
    """Return Postgres DSN built from environment variables."""
    return make_dsn(async_)


__all__ = ["build_url", "make_dsn"]
