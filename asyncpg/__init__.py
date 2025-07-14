from __future__ import annotations

from typing import Any, List


class _Pool:
    async def fetch(self, query: str, *args: Any) -> List[Any]:
        return []

    async def execute(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        return None

    async def close(self) -> None:
        return None


Pool = _Pool


async def create_pool(dsn: str) -> _Pool:
    """Return fake asyncpg pool for tests."""
    return _Pool()
