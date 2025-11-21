from __future__ import annotations

import pytest

from services.price_importer.services_common import llm


@pytest.mark.asyncio
async def test_generate_routes_to_providers(monkeypatch):
    calls: dict[str, object] = {}

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            calls["closed"] = True

        async def post_json(self, url, json, headers=None, timeout=None):
            calls["url"] = url
            calls["headers"] = headers
            return {"completion": "local", "choices": [{"message": {"content": "lan"}}]}

    monkeypatch.setattr(llm, "_llm_client", lambda integration: DummyClient())
    monkeypatch.setattr(llm, "LLM_PROVIDER", "local", raising=False)

    out_local = await llm.generate("prompt", provider="local")
    assert out_local == "local"
    assert calls["url"] == llm.LOCAL_URL

    out_lan = await llm.generate("prompt", provider="lan")
    assert out_lan == "lan"
    assert calls["url"].startswith(llm.LAN_BASE)
