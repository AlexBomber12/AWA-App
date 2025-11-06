import pytest

import awa_common.llm as llm


@pytest.mark.asyncio
async def test_switch_to_local(monkeypatch):
    async def fake_local(*a, **k):
        return "LOCAL"

    monkeypatch.setattr(llm, "_local_llm", fake_local)
    out = await llm.generate("hi", provider="local")
    assert out == "LOCAL"


@pytest.mark.asyncio
async def test_switch_to_openai(monkeypatch):
    async def fake_openai(*a, **k):
        return "GPT4o"

    monkeypatch.setattr(llm, "_openai_llm", fake_openai)
    out = await llm.generate("hi", provider="openai")
    assert out == "GPT4o"
