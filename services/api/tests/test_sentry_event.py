import os

import sentry_sdk
from fastapi.testclient import TestClient

# set env before importing app so init runs
os.environ["SENTRY_DSN"] = "http://public@selfhosted.invalid/1"
os.environ["SENTRY_ENV"] = "test"
os.environ["SENTRY_TRACES_SAMPLE_RATE"] = "0.0"
os.environ["SENTRY_PROFILES_SAMPLE_RATE"] = "0.0"

from services.api.main import app  # noqa: E402


class DummyTransport:
    def __init__(self, options):
        self.captured = []
        self.parsed_dsn = None

    def capture_event(self, event):
        self.captured.append(event)

    def flush(self, timeout=None, callback=None):  # pragma: no cover - test helper
        if callback:
            callback(0, True)
        return 0

    def capture_envelope(self, envelope):  # pragma: no cover - test helper
        pass

    def record_lost_event(self, *args, **kwargs):  # pragma: no cover - test helper
        pass

    def kill(self):  # pragma: no cover - test helper
        pass


def test_unhandled_exception_is_captured_and_tagged(monkeypatch):
    # install dummy transport
    hub = sentry_sdk.Hub.current
    if hub.client is not None:
        hub.client.transport = DummyTransport(hub.client.options)

    # inject a failing route
    def boom():
        raise RuntimeError("boom")

    app.add_api_route("/__boom", boom, methods=["GET"])

    with TestClient(app) as client:
        r = client.get("/__boom", headers={"X-Request-ID": "test-rid-123"})
        assert r.status_code == 500

    # verify captured event with tag
    tr = hub.client.transport
    assert isinstance(tr, DummyTransport)
    assert len(tr.captured) >= 1
    event = tr.captured[-1]
    assert event.get("tags", {}).get("request_id") == "test-rid-123"
