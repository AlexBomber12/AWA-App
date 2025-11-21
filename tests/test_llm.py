import types

import pytest

from awa_common import llm


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["lan", "openai"])
async def test_generate(monkeypatch, provider):
    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post_json(self, *_args, **_kwargs):
            return {"choices": [{"message": {"content": "hi"}}]}

    monkeypatch.setattr(llm, "_build_http_client", lambda timeout, integration: DummyClient())

    if provider == "openai":

        async def acreate(**_):
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="hi"))])

        openai = types.SimpleNamespace(ChatCompletion=types.SimpleNamespace(acreate=acreate))
        monkeypatch.setattr(llm.importlib, "import_module", lambda n: openai)

    res = await llm.generate("hi", provider=provider)
    assert res == "hi"
