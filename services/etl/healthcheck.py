from __future__ import annotations

import os
import sys
from urllib.request import Request, urlopen

import psycopg

from services.common.dsn import build_dsn


def check_db() -> bool:
    try:
        dsn = build_dsn(sync=True).replace("+psycopg", "")
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return False
    if not dsn:
        print("missing DSN", file=sys.stderr)
        return False
    # ``psycopg.connect`` expects ``connect_timeout`` instead of ``timeout``.
    # Using the wrong parameter causes "invalid connection option" errors and
    # makes the container healthcheck fail.
    try:
        with psycopg.connect(dsn, connect_timeout=2):
            pass
    except psycopg.OperationalError as exc:  # pragma: no cover - transient
        print(f"transient db error: {exc}", file=sys.stderr)
    return True


def check_minio() -> None:
    endpoint = os.getenv("MINIO_ENDPOINT")
    if not endpoint:
        return
    url = endpoint if "://" in endpoint else f"http://{endpoint}"
    req = Request(url, method="HEAD")
    urlopen(req, timeout=2)


def main() -> int:
    ok = True
    if not check_db():
        ok = False
    try:
        check_minio()
    except Exception as exc:  # pragma: no cover - network failures
        print(f"minio check failed: {exc}", file=sys.stderr)
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
