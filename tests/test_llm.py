import types

import pytest

from services.common import llm


class DummyResp:
    def __init__(self, json_data):
        self._data = json_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["lan", "openai"])
async def test_generate(monkeypatch, provider):
    async def fake_post(self, url, json=None, headers=None):
        return DummyResp({"choices": [{"message": {"content": "hi"}}]})

    monkeypatch.setattr(llm.httpx.AsyncClient, "post", fake_post)

    if provider == "openai":
        async def acreate(**_):
            return types.SimpleNamespace(
                choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="hi"))]
            )

        openai = types.SimpleNamespace(
            ChatCompletion=types.SimpleNamespace(acreate=acreate)
        )
        monkeypatch.setattr(llm.importlib, "import_module", lambda n: openai)

    res = await llm.generate("hi", provider=provider)
    assert res == "hi"
