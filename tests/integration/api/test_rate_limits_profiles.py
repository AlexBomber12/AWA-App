from __future__ import annotations

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

import services.api.main as api_main
from awa_common.db.async_session import get_async_session
from awa_common.security.models import Role, UserCtx
from awa_common.settings import settings
from services.api import roi_repository, security

pytestmark = pytest.mark.integration


class _DummyResult:
    def mappings(self):  # pragma: no cover - exercised via API
        return self

    def all(self):
        return [{"vendor": "acme", "roi_avg": 1.5, "items": 5}]


async def _fake_session():
    class _Session:
        async def execute(self, *_args, **_kwargs):
            return _DummyResult()

    yield _Session()


async def _fake_scores(_session, asins, _roi_view):
    return {asin: {"roi": 2.0, "vendor": "acme", "category": "books"} for asin in asins}


def _viewer_override(user: UserCtx):
    def _override(request: Request):
        request.state.user = user
        return user

    return _override


def _user() -> UserCtx:
    return UserCtx(
        sub="test-user", email="user@example.com", roles=[Role.viewer], raw_claims={"iss": settings.OIDC_ISSUER}
    )


def test_score_rate_limit_overlay(monkeypatch: pytest.MonkeyPatch):
    app = api_main.app
    user = _user()
    original = dict(app.dependency_overrides)
    app.dependency_overrides[get_async_session] = _fake_session
    monkeypatch.setattr(roi_repository, "fetch_scores_for_asins", _fake_scores, raising=True)
    app.dependency_overrides[security.require_viewer] = _viewer_override(user)
    try:
        with TestClient(app) as client:
            headers = {"Authorization": "Bearer token"}
            for idx in range(8):
                payload = {"asins": [f"B0000{idx}"]}
                resp = client.post("/score", json=payload, headers=headers)
                assert resp.status_code == 200
            resp = client.post("/score", json={"asins": ["B00999"]}, headers=headers)
            assert resp.status_code == 429
            assert resp.headers.get("Retry-After")
            assert resp.headers.get("X-RateLimit-Limit") == str(settings.RATE_LIMIT_SCORE_PER_USER)
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original)


def test_roi_by_vendor_overlay(monkeypatch: pytest.MonkeyPatch):
    app = api_main.app
    user = _user()
    original = dict(app.dependency_overrides)
    app.dependency_overrides[get_async_session] = _fake_session
    app.dependency_overrides[security.require_viewer] = _viewer_override(user)
    try:
        with TestClient(app) as client:
            for _idx in range(12):
                resp = client.get("/stats/roi_by_vendor")
                assert resp.status_code == 200
            resp = client.get("/stats/roi_by_vendor")
            assert resp.status_code == 429
            assert resp.headers.get("Retry-After")
            assert resp.headers.get("X-RateLimit-Limit") == str(settings.RATE_LIMIT_ROI_BY_VENDOR_PER_USER)
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original)


def test_invalid_jwt_fails_fast():
    with TestClient(api_main.app) as client:
        resp = client.post("/score", json={"asins": ["B00001"]}, headers={"Authorization": "Bearer invalid"})
        assert resp.status_code == 401
