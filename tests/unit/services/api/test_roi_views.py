import pytest

from services.api import roi_views


def test_get_roi_view_name_defaults(monkeypatch):
    monkeypatch.delenv("ROI_VIEW_NAME", raising=False)
    assert roi_views.get_roi_view_name() == roi_views.DEFAULT_ROI_VIEW


def test_get_roi_view_name_rejects_invalid(monkeypatch):
    monkeypatch.setenv("ROI_VIEW_NAME", "evil_view")
    with pytest.raises(roi_views.InvalidROIViewError):
        roi_views.get_roi_view_name()


def test_quote_identifier_supports_schema_names():
    quoted = roi_views.quote_identifier("public.v_roi_full")
    assert quoted == '"public"."v_roi_full"'
