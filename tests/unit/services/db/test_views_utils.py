from __future__ import annotations

import pytest

from services.db.utils import views


def test_quote_ident_handles_schema_and_escaping() -> None:
    assert views.quote_ident("public.my_view") == '"public"."my_view"'
    assert views.quote_ident('schema."strange"') == '"schema"."""strange"""'


def test_quote_ident_rejects_invalid_names() -> None:
    with pytest.raises(ValueError):
        views.quote_ident("")
    with pytest.raises(ValueError):
        views.quote_ident(".bad")


def test_render_create_view_constructs_statement() -> None:
    stmt = views.render_create_view("public.sample", "SELECT 1")
    assert stmt.startswith('CREATE OR REPLACE VIEW "public"."sample" AS')
    assert stmt.endswith("SELECT 1")


def test_render_drop_view_cascade_flag() -> None:
    assert views.render_drop_view("v_data") == 'DROP VIEW IF EXISTS "v_data" CASCADE;'
    assert views.render_drop_view("v_data", cascade=False) == 'DROP VIEW IF EXISTS "v_data";'


def test_replace_view_executes_drop_and_create(monkeypatch) -> None:
    calls: list[str] = []

    def _record(sql: str) -> None:
        calls.append(sql.strip())

    monkeypatch.setattr(views.op, "execute", _record)
    views.replace_view("v_demo", "CREATE VIEW v_demo AS SELECT 1")
    assert calls[0].startswith('DROP VIEW IF EXISTS "v_demo"')
    assert calls[1] == "CREATE VIEW v_demo AS SELECT 1"
