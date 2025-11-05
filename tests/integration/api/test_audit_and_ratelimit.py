from __future__ import annotations

import base64
import os

import psycopg
import pytest
import redis
from awa_common.settings import settings
from fastapi.testclient import TestClient

from services.api import main as api_main

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def _integration_auth_env():
    original_mode = settings.AUTH_MODE
    original_regex = getattr(settings, "AUTH_REQUIRED_ROUTES_REGEX", ".*")
    os.environ.setdefault("API_BASIC_USER", "integration-user")
    os.environ.setdefault("API_BASIC_PASS", "integration-pass")
    settings.AUTH_MODE = "basic"
    settings.AUTH_REQUIRED_ROUTES_REGEX = ".*"
    try:
        yield
    finally:
        settings.AUTH_MODE = original_mode
        settings.AUTH_REQUIRED_ROUTES_REGEX = original_regex


@pytest.fixture(scope="module")
def client(_integration_auth_env):
    with TestClient(api_main.app) as client:
        yield client


def _basic_headers() -> dict[str, str]:
    user = os.environ["API_BASIC_USER"]
    password = os.environ["API_BASIC_PASS"]
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _connect_db():
    dsn = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")
    return psycopg.connect(dsn)


def test_api_audit_rate_limit_persists_request(client):
    headers = _basic_headers()
    with _connect_db() as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE audit_log")
        conn.commit()

    resp = client.get("/ready", headers=headers)
    assert resp.status_code == 200

    with _connect_db() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT method, path, status, request_id FROM audit_log ORDER BY id DESC LIMIT 1"
        )
        row = cur.fetchone()
        assert row is not None, "audit_log should contain a persisted row"
        method, path, status, request_id = row
        assert method == "GET"
        assert path == "/ready"
        assert status == 200
        assert request_id


def test_api_audit_rate_limit_enforces_quota(client):
    headers = _basic_headers()
    redis_url = os.environ["REDIS_URL"]
    redis_client = redis.Redis.from_url(redis_url)
    redis_client.flushdb()

    for _ in range(5):
        resp = client.get("/ready", headers=headers)
        assert resp.status_code == 200

    throttled = client.get("/ready", headers=headers)
    assert throttled.status_code == 429

    redis_client.flushdb()
    reset = client.get("/ready", headers=headers)
    assert reset.status_code == 200
