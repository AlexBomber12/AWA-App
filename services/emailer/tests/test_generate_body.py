import pytest
from services.emailer import generate_body as gb


class DummyResp:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class DummyClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def post(self, url, json):
        return DummyResp({"completion": "ok"})


@pytest.mark.asyncio
async def test_local_llm(monkeypatch):
    monkeypatch.setattr(gb.httpx, "AsyncClient", lambda timeout=60: DummyClient())
    out = await gb.local_llm("hi")
    assert out == "ok"


@pytest.mark.asyncio
async def test_generate_body_local(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    async def fake_local(prompt: str, temp: float = 0.7, tokens: int = 256) -> str:
        return "local"

    monkeypatch.setattr(gb, "local_llm", fake_local)
    result = await gb.generate_body("prompt")
    assert result == "local"
