from __future__ import annotations

import types

from services.etl import fba_fee_ingestor as ingestor


def test_helium_helpers_use_settings(monkeypatch):
    cfg = types.SimpleNamespace(
        HELIUM10_BASE_URL="https://example.com",
        HELIUM10_TIMEOUT_S=12.0,
        HELIUM10_MAX_RETRIES=3,
        etl=None,
    )
    monkeypatch.setattr(ingestor, "settings", cfg, raising=False)
    assert ingestor._helium_base_url() == "https://example.com"
    assert ingestor._helium_timeout_s() == 12.0
    assert ingestor._helium_max_retries() == 3


def test_request_helium_fee_uses_client(monkeypatch):
    calls: dict[str, object] = {}

    class DummyClient:
        def get_json(self, path, headers=None):
            calls["path"] = path
            calls["headers"] = headers
            return {"totalFbaFee": 1.0}

        def close(self):
            calls["closed"] = True

    monkeypatch.setattr(ingestor, "_HTTP_CLIENT", DummyClient(), raising=False)
    data = ingestor._request_helium_fee({"Authorization": "Bearer x"}, "ASIN123")
    assert data["totalFbaFee"] == 1.0
    assert calls["path"].endswith("ASIN123")
    assert "Authorization" in calls["headers"]
