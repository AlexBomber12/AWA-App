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
        def __init__(self, *a, timeout=None, **kw):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **kw):
            class R:
                headers = {"content-type": "application/json"}

                def json(self):
                    return {"text": "ok"}

                @property
                def text(self):
                    return "ok"

                status_code = 200

                def raise_for_status(self):
                    pass

            return R()

    monkeypatch.setattr(
        llm,
        "httpx",
        types.SimpleNamespace(AsyncClient=FakeClient, TimeoutException=TimeoutError),
    )
    out = await llm.generate("hi")
    assert out == "ok"
    assert captured.get("timeout") == 0.1
