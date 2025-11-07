from __future__ import annotations

import os
import sys
import time
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen

import psycopg

from awa_common.dsn import build_dsn


def check_db() -> None:
    dsn = build_dsn(sync=True).replace("+psycopg", "")
    with psycopg.connect(dsn, connect_timeout=2) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")


def check_minio() -> None:
    endpoint = os.getenv("MINIO_ENDPOINT")
    if not endpoint:
        return
    # Normalize to include scheme
    url = endpoint if "://" in endpoint else f"http://{endpoint}"
    # Prefer MinIO's readiness endpoint which doesn't require auth
    try:
        parsed = urlparse(url)
        path = parsed.path or "/"
        if path in {"", "/"}:
            parsed = parsed._replace(path="/minio/health/ready")
            url = urlunparse(parsed)
    except Exception:
        pass
    req = Request(url, method="GET")
    urlopen(req, timeout=2)


def _retry(fn, attempts=3, delay=1.0, name="check") -> bool:
    for i in range(1, attempts + 1):
        try:
            fn()
            return True
        except Exception as exc:
            print(f"{name} attempt {i}/{attempts} failed: {exc}", file=sys.stderr)
            time.sleep(delay)
    return False


def main() -> int:
    ok = True
    if not _retry(check_db, name="db"):
        ok = False
    # Only check MinIO if configured (defaults to minio:9000 in compose)
    try:
        endpoint = os.getenv("MINIO_ENDPOINT", "").strip()
        if endpoint and not _retry(check_minio, name="minio"):
            ok = False
    except Exception as exc:
        print(f"minio setup failed: {exc}", file=sys.stderr)
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
