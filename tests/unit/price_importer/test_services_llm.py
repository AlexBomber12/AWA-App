from __future__ import annotations

import pytest

from services.price_importer.services_common import llm


@pytest.mark.asyncio
async def test_generate_wrapper(monkeypatch):
    called: dict[str, str] = {}

    async def fake_generate(prompt: str, temperature: float = 0.0, max_tokens: int = 0, provider: str | None = None):
        called["prompt"] = prompt
        called["provider"] = provider or "local"
        return "ok"

    monkeypatch.setattr(llm, "generate", fake_generate)
    out = await llm.generate("hello", provider="cloud")
    assert out == "ok"
    assert called["prompt"] == "hello"
    assert called["provider"] == "cloud"
