from __future__ import annotations

import os

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

import services.api.main as api_main
from awa_common.security.models import Role, UserCtx
from awa_common.settings import settings
from services.api import security
from tests.integration.test_audit_log import _connect_db

pytestmark = pytest.mark.integration


def test_api_audit_rate_limit_records_and_invokes_limiter():
    app = api_main.app
    original_overrides = dict(app.dependency_overrides)
    original_audit_flag = settings.SECURITY_ENABLE_AUDIT

    user = UserCtx(sub="audit-rate", email="audit-rate@example.com", roles=[Role.viewer], raw_claims={})
    limiter_calls: list[str] = []

    def viewer_override(request: Request) -> UserCtx:
        request.state.user = user
        return user

    def limiter_override() -> None:
        limiter_calls.append("viewer")
        return None

    app.dependency_overrides[security.require_viewer] = viewer_override
    app.dependency_overrides[security.limit_viewer] = limiter_override

    settings.SECURITY_ENABLE_AUDIT = True
    os.environ.setdefault("STATS_USE_SQL", "0")

    try:
        with TestClient(app) as client:
            with _connect_db() as conn, conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE audit_log")
                conn.commit()

            response = client.get("/stats/kpi")
            assert response.status_code == 200

            assert limiter_calls, "rate limiter dependency was not triggered"

            with _connect_db() as conn, conn.cursor() as cur:
                cur.execute("SELECT user_id, email, roles FROM audit_log ORDER BY id DESC LIMIT 1")
                row = cur.fetchone()
                assert row is not None
                user_id, email, roles = row
                assert user_id == user.sub
                assert email == user.email
                assert roles is None or "viewer" in str(roles)
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)
        settings.SECURITY_ENABLE_AUDIT = original_audit_flag
