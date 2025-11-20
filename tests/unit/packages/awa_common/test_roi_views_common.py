from types import SimpleNamespace

import pytest

from awa_common import roi_views
from awa_common.settings import Settings


@pytest.fixture(autouse=True)
def _reset_roi_cache():
    roi_views.clear_caches()
    yield
    roi_views.clear_caches()


def test_current_roi_view_defaults_to_expected_when_missing_config():
    cfg = SimpleNamespace()
    assert roi_views.current_roi_view(cfg=cfg, ttl_seconds=0) == roi_views.DEFAULT_ROI_VIEW


def test_current_roi_view_uses_configured_name(monkeypatch):
    monkeypatch.setenv("ROI_VIEW_NAME", " roi_view ")
    cfg = Settings()
    assert roi_views.current_roi_view(cfg=cfg, ttl_seconds=0) == "roi_view"


def test_current_roi_view_prefers_roi_group(monkeypatch):
    class DummyCfg:
        ROI_VIEW_NAME = ""
        roi = SimpleNamespace(view_name=" mat_v_roi_full ")

    monkeypatch.delenv("ROI_VIEW_NAME", raising=False)
    assert roi_views.current_roi_view(cfg=DummyCfg(), ttl_seconds=0) == "mat_v_roi_full"


def test_current_roi_view_rejects_invalid_config(monkeypatch):
    monkeypatch.setenv("ROI_VIEW_NAME", "evil_view")
    cfg = Settings()
    with pytest.raises(roi_views.InvalidROIViewError):
        roi_views.current_roi_view(cfg=cfg, ttl_seconds=0)


def test_current_roi_view_cache_and_clear(monkeypatch):
    cfg = SimpleNamespace(ROI_VIEW_NAME="v_roi_full")
    first = roi_views.current_roi_view(cfg=cfg, ttl_seconds=60)

    cfg.ROI_VIEW_NAME = "mat_v_roi_full"
    cached = roi_views.current_roi_view(cfg=cfg, ttl_seconds=60)
    assert cached == first

    refreshed = roi_views.current_roi_view(cfg=cfg, ttl_seconds=0)
    assert refreshed == "mat_v_roi_full"

    roi_views.clear_caches()
    cfg.ROI_VIEW_NAME = "roi_view"
    assert roi_views.current_roi_view(cfg=cfg, ttl_seconds=0) == "roi_view"
