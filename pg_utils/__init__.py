from __future__ import annotations

from typing import Any
import psycopg2


def connect(dsn: str) -> Any:
    """Wrapper around psycopg2.connect used for tests."""
    return psycopg2.connect(dsn)
