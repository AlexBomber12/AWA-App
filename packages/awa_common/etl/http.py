"""Shared HTTP client settings for ETL agents.

The environment variables documented below provide coarse control over
connection pooling, queue wait timeouts, and retry behaviour so long-running
agents can be tuned without code changes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _codes_env(name: str, default: tuple[int, ...]) -> tuple[int, ...]:
    raw = os.getenv(name)
    if not raw:
        return default
    values: set[int] = set()
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        try:
            values.add(int(token))
        except ValueError:
            continue
    return tuple(sorted(values)) if values else default


@dataclass(frozen=True)
class HTTPClientSettings:
    """Configuration knobs used by the shared httpx.AsyncClient.

    Defaults favour short-lived ETL bursts:
    - connect_timeout=5s, read_timeout=30s, total_timeout=60s
    - pool queue timeout=5s, max 100 total / 20 keep-alive connections
    - exponential retries (3 attempts) for 5xx + 429 responses
    """

    connect_timeout: float = _float_env("ETL_HTTP_CONNECT_TIMEOUT", 5.0)
    read_timeout: float = _float_env("ETL_HTTP_READ_TIMEOUT", 30.0)
    total_timeout: float = _float_env("ETL_HTTP_TOTAL_TIMEOUT", 60.0)
    pool_timeout: float = _float_env("ETL_HTTP_POOL_TIMEOUT", 5.0)
    max_connections: int = max(1, _int_env("ETL_HTTP_POOL_MAX_CONNECTIONS", 100))
    max_keepalive: int = max(0, _int_env("ETL_HTTP_POOL_MAX_KEEPALIVE", 20))
    retries: int = max(0, _int_env("ETL_HTTP_RETRIES", 3))
    retry_backoff_min: float = _float_env("ETL_HTTP_RETRY_BACKOFF_MIN", 0.25)
    retry_backoff_max: float = _float_env("ETL_HTTP_RETRY_BACKOFF_MAX", 5.0)
    retry_status_codes: tuple[int, ...] = _codes_env("ETL_HTTP_RETRY_STATUS_CODES", (408, 425, 429))
    follow_redirects: bool = os.getenv("ETL_HTTP_FOLLOW_REDIRECTS", "1").lower() not in {
        "0",
        "false",
        "no",
    }


http_settings = HTTPClientSettings()

__all__ = ["HTTPClientSettings", "http_settings"]
