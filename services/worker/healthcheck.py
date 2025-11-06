"""Celery service health checks: ensures worker can reach Redis and Postgres."""

from __future__ import annotations

import argparse
import sys
import time

import psycopg
import redis

from awa_common.settings import settings

from .celery_app import celery_app


def check_db() -> None:
    dsn = settings.DATABASE_URL.replace("+psycopg", "")
    with psycopg.connect(dsn, connect_timeout=2) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")


def check_redis() -> None:
    client = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2, socket_timeout=2)
    client.ping()


def ping_worker() -> None:
    try:
        if not celery_app.control.ping(timeout=2):
            print("no worker response", file=sys.stderr)
    except Exception as exc:
        print(f"ping failed: {exc}", file=sys.stderr)


def _retry(fn, attempts=3, delay=1.0, name="check") -> bool:
    for i in range(1, attempts + 1):
        try:
            fn()
            return True
        except Exception as exc:
            print(f"{name} attempt {i}/{attempts} failed: {exc}", file=sys.stderr)
            time.sleep(delay)
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("role", choices=["worker", "beat"])
    args = parser.parse_args(argv)

    ok = True
    if not _retry(check_redis, name="redis"):
        ok = False
    if not _retry(check_db, name="db"):
        ok = False
    if args.role == "worker":
        # optional – do not fail health on ping noise
        ping_worker()
    else:
        if not bool(getattr(celery_app.conf, "beat_schedule", None)):
            print("beat schedule missing", file=sys.stderr)
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
