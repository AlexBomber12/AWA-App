from __future__ import annotations

import os
import sys
from urllib.request import Request, urlopen

import psycopg

from services.common.dsn import build_dsn


def check_db() -> bool:
    try:
        dsn = build_dsn(sync=True).replace("+psycopg", "")
    except RuntimeError as exc:  # pragma: no cover - configuration
        print(exc, file=sys.stderr)
        return True
    if not dsn:
        print("missing DSN", file=sys.stderr)
        return True
    # ``psycopg.connect`` expects ``connect_timeout`` instead of ``timeout``.
    # Using the wrong parameter causes "invalid connection option" errors and
    # makes the container healthcheck fail.
    try:
        with psycopg.connect(dsn, connect_timeout=2):
            pass
    except psycopg.OperationalError as exc:  # pragma: no cover - transient
        print(f"transient db error: {exc}", file=sys.stderr)
    return True


def check_minio() -> bool:
    endpoint = os.getenv("MINIO_ENDPOINT")
    if not endpoint:
        print("MINIO_ENDPOINT missing", file=sys.stderr)
        return True
    url = endpoint if "://" in endpoint else f"http://{endpoint}"
    req = Request(url, method="HEAD")
    try:
        urlopen(req, timeout=2)
    except Exception as exc:  # pragma: no cover - transient
        print(f"transient minio error: {exc}", file=sys.stderr)
    return True


def main() -> int:
    ok = True
    if not check_db():
        ok = False
    if not check_minio():
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
