from collections.abc import Callable
from typing import cast

from awa_common.dsn import build_dsn as _raw_build_dsn

BuildDsnFn = Callable[..., str]
_build_dsn_typed: BuildDsnFn = cast(BuildDsnFn, _raw_build_dsn)


def make_dsn(async_: bool = False) -> str:
    """Return DSN using shared builder."""
    return _build_dsn_typed(sync=not async_)


def build_url(async_: bool = False) -> str:
    """Return Postgres DSN built from environment variables."""
    return make_dsn(async_)


__all__ = ["build_url", "make_dsn"]
