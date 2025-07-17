import asyncio
import importlib
import sys
import types


def test_import_emailer() -> None:
    sqlalchemy_stub = types.ModuleType("sqlalchemy")
    sqlalchemy_stub.orm = types.ModuleType("sqlalchemy.orm")
    sqlalchemy_stub.orm.declarative_base = lambda: None
    sys.modules.setdefault("sqlalchemy", sqlalchemy_stub)
    sys.modules.setdefault("sqlalchemy.orm", sqlalchemy_stub.orm)
    pkg = importlib.import_module("services.emailer")
    assert pkg.ping() == "pong"
    assert pkg.add(2, 3) == 5

    llm_stub = types.ModuleType("services.common.llm")

    async def _gen(prompt: str) -> str:
        return "OK"

    llm_stub.generate = _gen  # type: ignore[attr-defined]
    sys.modules["services.common.llm"] = llm_stub
    gb = importlib.import_module("services.emailer.generate_body")
    assert asyncio.run(gb.draft_email("x")) == "OK"
