from __future__ import annotations

import pytest
from sqlalchemy import inspect

from alembic.config import CommandLine


@pytest.mark.integration
def test_migration_roundtrip(db_engine) -> None:
    cli = CommandLine(prog="alembic")

    def run(*args: str) -> None:
        options = cli.parser.parse_args(["-c", "services/api/alembic.ini", *args])
        cli.run_cmd(options)

    def tables() -> list[str]:
        db_engine.dispose()
        return inspect(db_engine).get_table_names()

    run("downgrade", "base")
    assert not tables()

    run("upgrade", "head")
    upgraded = set(tables())
    assert "products" in upgraded

    run("downgrade", "base")
    assert not tables()

    run("upgrade", "head")
    assert set(tables()) == upgraded
