from types import SimpleNamespace

import pytest

from awa_common import roi_views


def test_current_roi_view_defaults(monkeypatch):
    roi_views.clear_caches()
    monkeypatch.setattr(roi_views.settings, "ROI_VIEW_NAME", roi_views.DEFAULT_ROI_VIEW, raising=False)
    assert roi_views.current_roi_view(ttl_seconds=0) == roi_views.DEFAULT_ROI_VIEW


def test_current_roi_view_rejects_invalid(monkeypatch):
    roi_views.clear_caches()
    monkeypatch.setattr(roi_views.settings, "ROI_VIEW_NAME", "evil_view", raising=False)
    with pytest.raises(roi_views.InvalidROIViewError):
        roi_views.current_roi_view(ttl_seconds=0)


def test_quote_identifier_supports_schema_names():
    quoted = roi_views.quote_identifier("public.v_roi_full")
    assert quoted == '"public"."v_roi_full"'


def test_current_roi_view_cache(monkeypatch):
    roi_views.clear_caches()
    monkeypatch.setattr(roi_views.settings, "ROI_VIEW_NAME", "v_roi_full", raising=False)
    first = roi_views.current_roi_view(ttl_seconds=60)
    monkeypatch.setattr(roi_views.settings, "ROI_VIEW_NAME", "mat_v_roi_full", raising=False)
    cached = roi_views.current_roi_view(ttl_seconds=60)
    assert first == cached  # cache hit
    refreshed = roi_views.current_roi_view(ttl_seconds=0)
    assert refreshed == "mat_v_roi_full"


def test_get_quoted_roi_view(monkeypatch):
    roi_views.clear_caches()
    monkeypatch.setattr(roi_views.settings, "ROI_VIEW_NAME", "v_roi_full", raising=False)
    roi_views.current_roi_view(ttl_seconds=0)
    assert roi_views.get_quoted_roi_view() == '"v_roi_full"'


def test_current_roi_view_respects_new_settings_instance(monkeypatch):
    from awa_common.settings import Settings

    monkeypatch.setenv("ROI_VIEW_NAME", "test_roi_view")
    cfg = Settings()
    roi_views.clear_caches()
    assert roi_views.current_roi_view(cfg=cfg, ttl_seconds=0) == "test_roi_view"


def test_current_roi_view_falls_back_to_roi_group(monkeypatch):
    class DummyCfg:
        roi = SimpleNamespace(view_name="roi_view")

    roi_views.clear_caches()
    assert roi_views.current_roi_view(cfg=DummyCfg(), ttl_seconds=0) == "roi_view"


def test_current_roi_view_falls_back_to_view_name_attr(monkeypatch):
    class DummyCfg:
        view_name = "mat_v_roi_full"

    roi_views.clear_caches()
    assert roi_views.current_roi_view(cfg=DummyCfg(), ttl_seconds=0) == "mat_v_roi_full"


def test_quote_identifier_rejects_empty_segments():
    with pytest.raises(roi_views.InvalidROIViewError):
        roi_views.quote_identifier("public..view")


def test_quote_identifier_rejects_empty_string():
    with pytest.raises(roi_views.InvalidROIViewError):
        roi_views.quote_identifier("")
