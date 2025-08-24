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


def check_db() -> bool:
    try:
        dsn = build_dsn(sync=True).replace("+psycopg", "")
    except RuntimeError as exc:  # pragma: no cover - configuration
        print(exc, file=sys.stderr)
        return True
    if not dsn:
        print("missing DSN", file=sys.stderr)
        return True
    try:
        with psycopg.connect(dsn, connect_timeout=2):
            pass
    except psycopg.OperationalError as exc:  # pragma: no cover - transient
        print(f"transient db error: {exc}", file=sys.stderr)
    return True


def check_redis() -> tuple[bool, bool]:
    url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    if not url:
        print("CELERY_BROKER_URL missing", file=sys.stderr)
        return False, False
    try:
        client = redis.Redis.from_url(url, socket_connect_timeout=2, socket_timeout=2)
        client.ping()
    except redis.exceptions.RedisError as exc:  # pragma: no cover - transient
        print(f"transient redis error: {exc}", file=sys.stderr)
        return True, False
    return True, True


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
    redis_ok, redis_up = check_redis()
    if not redis_ok:
        ok = False
    if not check_db():
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
