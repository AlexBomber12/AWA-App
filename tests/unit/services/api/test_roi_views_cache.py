import pytest

from services.api import roi_views


def test_get_roi_view_name_uses_cache(monkeypatch):
    calls = {"count": 0}

    def _fake_current_roi_view():
        calls["count"] += 1
        return "v_roi_full"

    monkeypatch.setenv(roi_views.ROI_CACHE_TTL_ENV, "300")
    roi_views.clear_caches()
    monkeypatch.setattr(roi_views, "current_roi_view", _fake_current_roi_view)

    first = roi_views.get_roi_view_name()
    second = roi_views.get_roi_view_name()

    assert first == "v_roi_full"
    assert second == "v_roi_full"
    assert calls["count"] == 1


class _DummyScalar:
    def __init__(self, value: int):
        self._value = value

    def scalar(self):
        return self._value


class _DummySession:
    def __init__(self, scalar_value: int = 1):
        self.scalar_value = scalar_value
        self.calls = 0

    async def execute(self, stmt):
        self.calls += 1
        return _DummyScalar(self.scalar_value)


@pytest.mark.asyncio
async def test_returns_vendor_column_check_cached(monkeypatch):
    monkeypatch.setenv(roi_views.ROI_CACHE_TTL_ENV, "300")
    roi_views.clear_caches()
    session = _DummySession(scalar_value=1)

    first = await roi_views.returns_vendor_column_exists(session, table_name="returns_raw", schema="public")
    second = await roi_views.returns_vendor_column_exists(session, table_name="returns_raw", schema="public")

    assert first is True
    assert second is True
    assert session.calls == 1
