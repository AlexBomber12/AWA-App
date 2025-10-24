import asyncio
import importlib
import sys


def test_import_emailer() -> None:
    pkg = importlib.import_module("services.emailer")
    assert pkg.ping() == "pong"
    assert pkg.add(2, 3) == 5

    llm_stub = importlib.import_module("awa_common.llm")

    async def _gen(prompt: str) -> str:
        return "OK"

    llm_stub.generate = _gen  # type: ignore[attr-defined]

    sys.modules.pop("services.emailer.generate_body", None)
    gb = importlib.import_module("services.emailer.generate_body")
    assert asyncio.run(gb.draft_email("x")) == "OK"
