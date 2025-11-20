import pytest

from services.api import roi_views


@pytest.fixture(autouse=True)
def _reset_roi_cache():
    roi_views.clear_caches()
    yield
    roi_views.clear_caches()


class _DummyScalar:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value


class _DummySession:
    def __init__(self, scalar_value=None, exc: Exception | None = None):
        self.scalar_value = scalar_value
        self.exc = exc
        self.calls = 0

    async def execute(self, stmt):
        self.calls += 1
        if self.exc:
            raise self.exc
        return _DummyScalar(self.scalar_value)


@pytest.mark.asyncio
async def test_returns_vendor_column_check_cached_true():
    session = _DummySession(scalar_value="vendor")

    first = await roi_views.returns_vendor_column_exists(session, table_name="returns_raw", schema="public")
    second = await roi_views.returns_vendor_column_exists(session, table_name="returns_raw", schema="public")

    assert first is True
    assert second is True
    assert session.calls == 1


@pytest.mark.asyncio
async def test_returns_vendor_column_check_cached_false():
    session = _DummySession(scalar_value=None)

    first = await roi_views.returns_vendor_column_exists(session, table_name="returns_raw", schema="public")
    second = await roi_views.returns_vendor_column_exists(session, table_name="returns_raw", schema="public")

    assert first is False
    assert second is False
    assert session.calls == 1


@pytest.mark.asyncio
async def test_returns_vendor_column_check_handles_errors(monkeypatch):
    logger_calls = []

    class _Logger:
        def warning(self, *args, **kwargs):
            logger_calls.append((args, kwargs))

    monkeypatch.setattr(roi_views, "logger", _Logger())
    session = _DummySession(exc=RuntimeError("boom"))

    result = await roi_views.returns_vendor_column_exists(session, table_name="returns_raw", schema="public")
    cached = await roi_views.returns_vendor_column_exists(session, table_name="returns_raw", schema="public")

    assert result is False
    assert cached is False
    assert session.calls == 1
    assert logger_calls, "Expected error to be logged"
