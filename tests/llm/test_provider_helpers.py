import importlib
import types

import pytest


@pytest.mark.asyncio
async def test_timeout_env_changes_timeout_used(monkeypatch):
    llm = importlib.reload(importlib.import_module("awa_common.llm"))
    settings_stub = types.SimpleNamespace(
        llm=types.SimpleNamespace(
            provider="local",
            fallback_provider="stub",
            request_timeout_s=0.1,
            local_url="http://llm:8000/llm",
            lan_api_base_url="http://localhost:8000",
            lan_health_base_url="http://lan-llm:8000",
            lan_health_timeout_s=1.0,
            lan_api_key=None,
            remote_url=None,
            openai_model="gpt-4o-mini",
            openai_api_key=None,
            openai_api_base=None,
        )
    )
    monkeypatch.setattr(llm, "_settings", settings_stub)
    captured: dict[str, float | None] = {}

    class FakeClient:
        def __init__(self, *a, integration=None, total_timeout_s=None, max_retries=None, **kw):
            captured["client_timeout"] = total_timeout_s

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post_json(self, *a, **kw):
            captured["request_timeout"] = kw.get("timeout")
            return {"text": "ok"}

    monkeypatch.setattr(llm, "AsyncHTTPClient", FakeClient)
    out = await llm.generate("hi")
    assert out == "ok"
    assert captured.get("client_timeout") == 0.1
    assert captured.get("request_timeout") == 0.1
