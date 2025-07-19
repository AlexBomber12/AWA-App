import os

import pytest
from httpx import Response

from services.common.llm import generate

respx = pytest.importorskip("respx")


@respx.mock
@pytest.mark.asyncio
async def test_generate_via_lan(monkeypatch):
    os.environ["LLM_PROVIDER"] = "lan"
    os.environ["LLM_BASE_URL"] = "http://192.168.0.4:8000"
    route = respx.post("http://192.168.0.4:8000/v1/chat/completions").mock(
        return_value=Response(200, json={"choices": [{"message": {"content": "hi"}}]})
    )
    out = await generate("hi", max_tokens=8)
    assert route.called
    assert out == "hi"
