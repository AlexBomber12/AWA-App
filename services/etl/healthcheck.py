"""ETL service health checks.

Ensures the process can reach PostgreSQL and MinIO before reporting healthy.
"""

from __future__ import annotations

import os
import sys
import time
from urllib.request import Request, urlopen

import psycopg

from services.common.dsn import build_dsn


def check_db() -> None:
    dsn = build_dsn(sync=True).replace("+psycopg", "")
    if not dsn:
        raise RuntimeError("missing DSN")
    # ``psycopg.connect`` expects ``connect_timeout`` instead of ``timeout``.
    with psycopg.connect(dsn, connect_timeout=2):
        pass


def check_minio() -> None:
    endpoint = os.getenv("MINIO_ENDPOINT")
    if not endpoint:
        raise RuntimeError("MINIO_ENDPOINT missing")
    url = endpoint if "://" in endpoint else f"http://{endpoint}"
    req = Request(url, method="HEAD")
    urlopen(req, timeout=2)


def _retry(fn, attempts: int = 3, delay: float = 1.0, name: str = "check") -> bool:
    for i in range(1, attempts + 1):
        try:
            fn()
            return True
        except Exception as exc:  # pragma: no cover - transient
            print(f"{name} attempt {i}/{attempts} failed: {exc}", file=sys.stderr)
            time.sleep(delay)
    return False


def main() -> int:
    ok = True
    if not _retry(check_db, name="db"):
        ok = False
    try:
        endpoint = os.getenv("MINIO_ENDPOINT", "").strip()
        if endpoint and not _retry(check_minio, name="minio"):
            ok = False
    except Exception as exc:  # pragma: no cover - misconfiguration
        print(f"minio setup failed: {exc}", file=sys.stderr)
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
