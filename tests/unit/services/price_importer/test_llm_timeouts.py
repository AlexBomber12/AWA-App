import pytest

from services.price_importer.services_common import llm as llm_module


@pytest.mark.asyncio
async def test_local_llm_uses_configured_timeout(monkeypatch):
    captured = {}

    class DummyResponse:
        def __init__(self):
            self._payload = {"completion": "ok"}

        def raise_for_status(self):
            pass

        def json(self):
            return self._payload

    class DummyClient:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, *args, **kwargs):
            return DummyResponse()

    monkeypatch.setattr(llm_module, "httpx", type("HX", (), {"AsyncClient": DummyClient}))
    llm_module.LLM_TIMEOUT_S = 12.0
    result = await llm_module._local_llm("prompt", 0.1, 10)
    assert result == "ok"
    assert captured["timeout"] == 12.0


@pytest.mark.asyncio
async def test_remote_generate_honors_timeout(monkeypatch):
    captured = {}

    class DummyResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "remote"}}]}

    class DummyClient:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, *args, **kwargs):
            captured["payload"] = kwargs
            return DummyResponse()

    monkeypatch.setattr(llm_module, "httpx", type("HX", (), {"AsyncClient": DummyClient}))
    llm_module.LLM_TIMEOUT_S = 7.0
    result = await llm_module._remote_generate("http://base", "key", "prompt", 16, "model")
    assert result == "remote"
    assert captured["timeout"] == 7.0
