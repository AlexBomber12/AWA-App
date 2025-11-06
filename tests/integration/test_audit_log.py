from __future__ import annotations

import os

import psycopg
import pytest
from fastapi import Request
from fastapi.testclient import TestClient

import services.api.main as api_main
from awa_common.security.models import Role, UserCtx
from awa_common.settings import settings
from services.api import security

pytestmark = pytest.mark.integration


def _connect_db():
    dsn = settings.DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    return psycopg.connect(dsn)


@pytest.fixture
def audit_client(monkeypatch: pytest.MonkeyPatch):
    app = api_main.app

    original_overrides = dict(app.dependency_overrides)

    user = UserCtx(sub="auditor", email="audit@example.com", roles=[Role.viewer], raw_claims={})

    def viewer_override(request: Request):
        request.state.user = user
        return user

    app.dependency_overrides[security.require_viewer] = viewer_override
    app.dependency_overrides[security.limit_viewer] = lambda: None
    app.dependency_overrides[security.limit_ops] = lambda: None
    app.dependency_overrides[security.limit_admin] = lambda: None

    settings.SECURITY_ENABLE_AUDIT = True
    os.environ.setdefault("STATS_USE_SQL", "0")

    with TestClient(app) as client:
        yield client, user

    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)


def test_audit_log_records_authenticated_request(audit_client):
    client, user = audit_client
    with _connect_db() as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE audit_log")
        conn.commit()

    resp = client.get("/stats/kpi")
    assert resp.status_code == 200

    with _connect_db() as conn, conn.cursor() as cur:
        cur.execute("SELECT user_id, email, roles, request_id FROM audit_log ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        assert row is not None
        user_id, email, roles, request_id = row
        assert user_id == user.sub
        assert email == user.email
        assert request_id
        assert roles is None or "viewer" in str(roles)


def test_audit_log_skips_health(audit_client):
    client, _ = audit_client
    with _connect_db() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM audit_log")
        before = cur.fetchone()[0]

    resp = client.get("/health")
    assert resp.status_code == 200

    with _connect_db() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM audit_log")
        after = cur.fetchone()[0]
    assert after == before
