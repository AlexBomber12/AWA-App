import pytest
from services.emailer import generate_body as gb


@pytest.mark.asyncio
async def test_draft_email(monkeypatch):
    async def fake_generate(prompt: str):
        return "EMAIL"

    monkeypatch.setattr(gb, "generate", fake_generate)
    out = await gb.draft_email("hello")
    assert out == "EMAIL"
