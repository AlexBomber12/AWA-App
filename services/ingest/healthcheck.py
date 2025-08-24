"""Celery service health checks.

Ensures the worker can reach Redis and PostgreSQL before reporting healthy.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import psycopg
import redis

from services.common.dsn import build_dsn

from .celery_app import celery_app


def _retry(fn, attempts: int = 3, delay: float = 1.0, name: str = "check") -> bool:
    for i in range(1, attempts + 1):
        try:
            fn()
            return True
        except Exception as exc:  # pragma: no cover - transient
            print(f"{name} attempt {i}/{attempts} failed: {exc}", file=sys.stderr)
            time.sleep(delay)
    return False


def check_db() -> None:
    dsn = build_dsn(sync=True).replace("+psycopg", "")
    if not dsn:
        raise RuntimeError("missing DSN")
    with psycopg.connect(dsn, connect_timeout=2):
        pass


def check_redis() -> None:
    url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    if not url:
        raise RuntimeError("CELERY_BROKER_URL missing")
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
    redis_up = _retry(check_redis, name="redis")
    if not redis_up:
        ok = False
    if not _retry(check_db, name="db"):
        ok = False
    if args.role == "worker" and redis_up:
        ping_worker()
    elif args.role == "beat":
        if not check_beat_schedule():
            print("beat schedule missing", file=sys.stderr)
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
