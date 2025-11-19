from __future__ import annotations

import sys
import time
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen

import psycopg

from awa_common.dsn import build_dsn
from awa_common.settings import settings


def _db_timeout() -> float:
    return float(getattr(settings, "HEALTHCHECK_DB_TIMEOUT_S", 2.0))


def _http_timeout() -> float:
    return float(getattr(settings, "HEALTHCHECK_HTTP_TIMEOUT_S", 2.0))


def _retry_budget() -> tuple[int, float]:
    attempts = int(getattr(settings, "HEALTHCHECK_RETRY_ATTEMPTS", 3) or 3)
    delay = float(getattr(settings, "HEALTHCHECK_RETRY_DELAY_S", 1.0) or 1.0)
    return max(attempts, 1), max(delay, 0.0)


def check_db() -> None:
    dsn = build_dsn(sync=True).replace("+psycopg", "")
    with psycopg.connect(dsn, connect_timeout=_db_timeout()) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")


def check_minio() -> None:
    s3_cfg = getattr(settings, "s3", None)
    endpoint = s3_cfg.endpoint if s3_cfg else ""
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
    urlopen(req, timeout=_http_timeout())


def _retry(fn, attempts=None, delay=None, name="check") -> bool:
    default_attempts, default_delay = _retry_budget()
    attempts = int(attempts or default_attempts)
    delay = float(delay if delay is not None else default_delay)
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
        s3_cfg = getattr(settings, "s3", None)
        endpoint = (s3_cfg.endpoint if s3_cfg else "").strip()
        if endpoint and not _retry(check_minio, name="minio"):
            ok = False
    except Exception as exc:
        print(f"minio setup failed: {exc}", file=sys.stderr)
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
