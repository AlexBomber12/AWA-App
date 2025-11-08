from collections.abc import Callable
from typing import cast

from awa_common.dsn import build_dsn as _raw_build_dsn

BuildDsnFn = Callable[..., str]
_build_dsn_typed: BuildDsnFn = cast(BuildDsnFn, _raw_build_dsn)


def build_url(async_: bool = True) -> str:
    """Return Postgres DSN from environment variables."""
    return _build_dsn_typed(sync=not async_)


__all__ = ["build_url"]
