from __future__ import annotations

import io

import pytest
from alembic import command
from alembic.config import CommandLine, Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text


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

    cfg = Config("services/api/alembic.ini")
    buffer = io.StringIO()
    cfg.print_stdout = buffer.write  # type: ignore[assignment]
    command.current(cfg)
    head_revision = ScriptDirectory.from_config(cfg).get_current_head()
    current_output = buffer.getvalue().strip()
    assert head_revision and head_revision in current_output

    with db_engine.connect() as conn:
        roi_view_exists = conn.execute(text("SELECT to_regclass('roi_view')")).scalar()
        refunds_mv_exists = conn.execute(text("SELECT to_regclass('v_refund_totals')")).scalar()
        assert roi_view_exists
        assert refunds_mv_exists
