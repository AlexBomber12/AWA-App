import pytest

from awa_common import roi_views


def test_current_roi_view_defaults(monkeypatch):
    monkeypatch.delenv("ROI_VIEW_NAME", raising=False)
    assert roi_views.current_roi_view(ttl_seconds=0) == roi_views.DEFAULT_ROI_VIEW


def test_current_roi_view_rejects_invalid(monkeypatch):
    monkeypatch.setenv("ROI_VIEW_NAME", "evil_view")
    with pytest.raises(roi_views.InvalidROIViewError):
        roi_views.current_roi_view(ttl_seconds=0)


def test_quote_identifier_supports_schema_names():
    quoted = roi_views.quote_identifier("public.v_roi_full")
    assert quoted == '"public"."v_roi_full"'


def test_current_roi_view_cache(monkeypatch):
    monkeypatch.setenv("ROI_VIEW_NAME", "v_roi_full")
    first = roi_views.current_roi_view(ttl_seconds=60)
    monkeypatch.setenv("ROI_VIEW_NAME", "mat_v_roi_full")
    cached = roi_views.current_roi_view(ttl_seconds=60)
    assert first == cached  # cache hit
    refreshed = roi_views.current_roi_view(ttl_seconds=0)
    assert refreshed == "mat_v_roi_full"
