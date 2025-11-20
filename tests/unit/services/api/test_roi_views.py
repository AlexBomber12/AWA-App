import pytest

from services.api import roi_views


@pytest.fixture(autouse=True)
def _reset_roi_views_cache():
    roi_views.clear_caches()
    yield
    roi_views.clear_caches()


def test_get_roi_view_name_delegates_to_common(monkeypatch):
    calls = {"count": 0}

    def _fake_current_roi_view():
        calls["count"] += 1
        return "roi_view"

    monkeypatch.setattr(roi_views, "current_roi_view", _fake_current_roi_view)

    assert roi_views.get_roi_view_name() == "roi_view"
    assert roi_views.get_roi_view_name() == "roi_view"
    assert calls["count"] == 2


def test_get_quoted_roi_view_uses_quote_identifier(monkeypatch):
    monkeypatch.setattr(roi_views, "current_roi_view", lambda: "roi_view")
    captured: dict[str, str] = {}

    def _quote(identifier: str) -> str:
        captured["value"] = identifier
        return f"<{identifier}>"

    monkeypatch.setattr(roi_views, "quote_identifier", _quote)

    assert roi_views.get_quoted_roi_view() == "<roi_view>"
    assert captured["value"] == "roi_view"


def test_get_quoted_roi_view_quotes_schema_names(monkeypatch):
    monkeypatch.setattr(roi_views, "current_roi_view", lambda: "public.v_roi_full")
    assert roi_views.get_quoted_roi_view() == '"public"."v_roi_full"'
