from __future__ import annotations

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import event

import services.api.main as api_main
from awa_common.db.async_session import get_async_engine
from awa_common.security.models import Role, UserCtx
from services.api import security

pytestmark = pytest.mark.integration


def _viewer_override(request: Request) -> UserCtx:
    user = UserCtx(sub="score-tester", email="score@test", roles=[Role.viewer], raw_claims={})
    request.state.user = user
    return user


def test_score_query_efficiency(monkeypatch: pytest.MonkeyPatch):
    app = api_main.app
    original_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[security.require_viewer] = _viewer_override
    app.dependency_overrides[security.limit_viewer] = lambda: None

    engine = get_async_engine()
    statements: list[str] = []

    def _count_statements(conn, cursor, statement, parameters, context, executemany):  # noqa: ARG001
        if statement.strip().upper().startswith("SELECT 1"):
            return
        statements.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", _count_statements)
    try:
        with TestClient(app) as client:
            resp = client.post("/score", json={"asins": ["ZX-1", "ZX-2", "ZX-3"]})
            assert resp.status_code == 200
        assert len(statements) <= 2
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", _count_statements)
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)
