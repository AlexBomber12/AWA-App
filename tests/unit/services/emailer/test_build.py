from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_draft_email_uses_template_values(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.emailer import generate_body

    template = Path("tests/fixtures/email/body_template.txt").read_text(encoding="utf-8")
    prompts: list[str] = []

    async def fake_generate(prompt: str) -> str:
        prompts.append(prompt)
        return "Rendered body"

    monkeypatch.setattr(generate_body, "generate", fake_generate)

    result = await generate_body.draft_email(
        template.format(customer="\u0410\u043d\u043d\u0430", order_id="ORD-42", total="19.99")
    )

    assert result == "Rendered body"
    assert "ORD-42" in prompts[0]
    assert "\u0410\u043d\u043d\u0430" in prompts[0]


@pytest.mark.asyncio
async def test_draft_email_accepts_empty_body(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.emailer import generate_body

    async def fake_generate(prompt: str) -> str:
        assert prompt == ""
        return ""

    monkeypatch.setattr(generate_body, "generate", fake_generate)

    assert await generate_body.draft_email("") == ""


@pytest.mark.asyncio
async def test_draft_email_rejects_non_string_responses(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.emailer import generate_body

    async def fake_generate(prompt: str):
        return {"text": prompt}

    monkeypatch.setattr(generate_body, "generate", fake_generate)

    with pytest.raises(TypeError):
        await generate_body.draft_email("payload")


def test_emailer_exports_simple_helpers() -> None:
    from services import emailer

    assert emailer.ping() == "pong"
    assert emailer.add(2, 3) == 5
