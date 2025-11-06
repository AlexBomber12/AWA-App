from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any
from urllib.parse import quote, urlencode

DEFAULT_PORT = {
    "postgresql": 5432,
    "postgres": 5432,
    "mysql": 3306,
    "mariadb": 3306,
    "redis": 6379,
    "amqp": 5672,
}

_POSTGRES_SCHEMES = {"postgresql", "postgres"}
_SYNC_DRIVER = "psycopg"
_ASYNC_DRIVER = "asyncpg"


def _bracket_ipv6(host: str) -> str:
    if ":" in host and not (host.startswith("[") and host.endswith("]")):
        return f"[{host}]"
    return host


def _first_env(*names: str, default: str | None = None) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


def _normalize_driver(sync: bool | None, driver: str | None) -> tuple[bool | None, str | None]:
    norm = driver.lower() if driver else None
    if norm in {_SYNC_DRIVER, _ASYNC_DRIVER}:
        sync = norm == _SYNC_DRIVER
    elif norm:
        return sync, norm
    if sync is not None and norm is None:
        norm = _SYNC_DRIVER if sync else _ASYNC_DRIVER
    return sync, norm


def _apply_postgres_driver(url: str, sync: bool | None, driver: str | None) -> str:
    scheme, sep, rest = url.partition("://")
    if not sep:
        return url
    base = scheme
    existing_driver = None
    if "+" in scheme:
        base, existing_driver = scheme.split("+", 1)
    base_lower = base.lower()
    if base_lower not in _POSTGRES_SCHEMES:
        if driver and "+" not in scheme:
            return f"{scheme}+{driver}://{rest}"
        return url

    target_driver = driver or existing_driver
    if sync is not None:
        target_driver = _SYNC_DRIVER if sync else _ASYNC_DRIVER
    if target_driver:
        return f"{base}+{target_driver}://{rest}"
    return f"{base}://{rest}"


def _build_from_parts(
    scheme: str,
    host: str = "localhost",
    port: int | str | None = None,
    user: str | None = None,
    password: str | None = None,
    database: str | None = None,
    params: Mapping[str, Any] | None = None,
    sync: bool | None = None,
    driver: str | None = None,
) -> str:
    auth = ""
    if user:
        encoded_user = quote(str(user))
        if password is not None:
            auth = f"{encoded_user}:{quote(str(password))}@"
        else:
            auth = f"{encoded_user}@"
    host_part = _bracket_ipv6(host)
    base_scheme = scheme.split("+", 1)[0]
    eff_port = int(port) if port not in (None, "", 0) else DEFAULT_PORT.get(base_scheme)
    port_part = f":{eff_port}" if eff_port else ""
    db_part = f"/{database}" if database else ""
    query_part = ""
    if params:
        query_part = "?" + urlencode({k: v for k, v in params.items() if v is not None}, doseq=True)
    url = f"{scheme}://{auth}{host_part}{port_part}{db_part}{query_part}"
    if base_scheme.lower() in _POSTGRES_SCHEMES:
        return _apply_postgres_driver(url, sync, driver)
    return url


def _build_from_env(sync: bool | None, driver: str | None) -> str:
    sync, driver = _normalize_driver(sync, driver)
    order = []
    if sync is True:
        order.append("PG_SYNC_DSN")
    elif sync is False:
        order.append("PG_ASYNC_DSN")
    if driver == _SYNC_DRIVER:
        order.append("PG_SYNC_DSN")
    if driver == _ASYNC_DRIVER:
        order.append("PG_ASYNC_DSN")
    order.extend(["DATABASE_URL", "PG_ASYNC_DSN", "PG_SYNC_DSN"])

    seen: set[str] = set()
    for name in order:
        if name in seen:
            continue
        seen.add(name)
        value = os.getenv(name)
        if value:
            return _apply_postgres_driver(value, sync, driver)

    host = _first_env("PG_HOST", "POSTGRES_HOST", default="localhost")
    port = _first_env("PG_PORT", "POSTGRES_PORT", default=str(DEFAULT_PORT["postgresql"]))
    user = _first_env("PG_USER", "POSTGRES_USER")
    password = _first_env("PG_PASSWORD", "POSTGRES_PASSWORD")
    database = _first_env("PG_DATABASE", "POSTGRES_DB")

    return _build_from_parts(
        "postgresql",
        host=host or "localhost",
        port=port,
        user=user,
        password=password,
        database=database,
        sync=sync,
        driver=driver,
    )


def build_dsn(
    scheme: str | None = None,
    host: str = "localhost",
    port: int | str | None = None,
    user: str | None = None,
    password: str | None = None,
    database: str | None = None,
    params: Mapping[str, Any] | None = None,
    *,
    sync: bool | None = None,
    driver: str | None = None,
) -> str:
    """Return a connection string assembled from explicit parts or environment variables.

    When ``scheme`` is not provided the function inspects common database
    environment variables and normalises Postgres URLs so synchronous callers
    receive a ``+psycopg`` suffix while async callers receive ``+asyncpg``.
    """

    if scheme is None:
        return _build_from_env(sync=sync, driver=driver)
    return _build_from_parts(
        scheme,
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        params=params,
        sync=sync,
        driver=driver,
    )


__all__ = ["build_dsn"]
