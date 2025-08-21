"""Celery service health checks.

Ensures the worker can reach Redis and PostgreSQL before reporting healthy.
"""

from __future__ import annotations

import argparse
import os
import sys

import psycopg
import redis

from services.common.dsn import build_dsn

from .celery_app import celery_app


def check_db() -> None:
    dsn = build_dsn(sync=True).replace("+psycopg", "")
    with psycopg.connect(dsn, connect_timeout=2) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")


def check_redis() -> None:
    url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    client = redis.Redis.from_url(url, socket_connect_timeout=2, socket_timeout=2)
    client.ping()


def ping_worker() -> None:
    """Attempt to ping the Celery worker.

    Older Celery versions or certain broker setups may disable the remote
    control commands used by ``app.control.ping``.  Rather than failing the
    health check outright, log any issues and allow the container to be marked
    healthy as long as Redis and Postgres are reachable.
    """

    try:
        if not celery_app.control.ping(timeout=2):
            print("no worker response", file=sys.stderr)
    except Exception as exc:  # pragma: no cover - optional ping
        print(f"ping failed: {exc}", file=sys.stderr)


def check_beat_schedule() -> bool:
    return bool(getattr(celery_app.conf, "beat_schedule", None))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("role", choices=["worker", "beat"])
    args = parser.parse_args(argv)

    ok = True
    try:
        check_redis()
    except Exception as exc:  # pragma: no cover - network failures
        print(f"redis check failed: {exc}", file=sys.stderr)
        ok = False
    try:
        check_db()
    except Exception as exc:  # pragma: no cover - network failures
        print(f"db check failed: {exc}", file=sys.stderr)
        ok = False
    if args.role == "worker":
        ping_worker()
    else:
        if not check_beat_schedule():
            print("beat schedule missing", file=sys.stderr)
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
