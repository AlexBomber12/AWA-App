from __future__ import annotations

import ast
import contextlib
import io
import os
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url

from awa_common.dsn import build_dsn
from awa_common.settings import settings

pytestmark = pytest.mark.integration


def test_migrations_are_current(monkeypatch: pytest.MonkeyPatch) -> None:
    with _temporary_database(monkeypatch) as database_url:
        cfg = _configured_alembic_config(database_url)
        command.upgrade(cfg, "head")

        history_output = _capture_history(cfg)
        script_dir = ScriptDirectory.from_config(cfg)
        head_revision = script_dir.get_current_head()
        assert head_revision, "Alembic could not determine the head revision"
        assert head_revision in history_output, "alembic history --verbose did not include the head revision"
        assert _current_db_revision(database_url) == head_revision, "Database version does not match Alembic head"

        assert_no_schema_changes(cfg)


def assert_no_schema_changes(cfg: Config) -> None:
    """Autogenerate a throwaway revision and ensure it contains no operations."""

    rev_id = f"migration_guard_{uuid.uuid4().hex[:10]}"
    scripts = command.revision(
        cfg,
        message="migration currency check",
        autogenerate=True,
        rev_id=rev_id,
    )
    created_paths = _collect_script_paths(scripts)
    try:
        for path in created_paths:
            _assert_revision_noop(path)
    finally:
        for path in created_paths:
            path.unlink(missing_ok=True)


def _assert_revision_noop(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    for func_name in ("upgrade", "downgrade"):
        func = functions.get(func_name)
        if func is None or not _function_body_is_noop(func):
            raise AssertionError(f"{path.name}: {func_name}() contains schema changes")


def _function_body_is_noop(func: ast.FunctionDef) -> bool:
    for node in func.body:
        if isinstance(node, ast.Pass):
            continue
        if isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant):
            continue
        return False
    return True


def _collect_script_paths(scripts: Any) -> list[Path]:
    if scripts is None:
        return []
    if isinstance(scripts, list):
        return [Path(script.path) for script in scripts if script is not None]
    return [Path(scripts.path)]


@contextlib.contextmanager
def _temporary_database(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    base_url = _base_sync_url()
    temp_name = f"awa_migrations_{uuid.uuid4().hex[:8]}"
    admin_url = base_url.set(database="postgres")
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{temp_name}"'))
            conn.execute(text(f'CREATE DATABASE "{temp_name}" TEMPLATE template0'))
        temp_url = base_url.set(database=temp_name)
        sync_url = str(temp_url)
        _apply_database_env(monkeypatch, sync_url, temp_name)
        yield sync_url
    finally:
        with admin_engine.connect() as conn:
            conn.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :dbname AND pid <> pg_backend_pid()"
                ),
                {"dbname": temp_name},
            )
            conn.execute(text(f'DROP DATABASE IF EXISTS "{temp_name}"'))
        admin_engine.dispose()


def _apply_database_env(monkeypatch: pytest.MonkeyPatch, sync_url: str, db_name: str) -> None:
    monkeypatch.setenv("DATABASE_URL", sync_url)
    monkeypatch.setenv("PG_DATABASE", db_name)
    monkeypatch.setenv("PG_SYNC_DSN", sync_url)
    monkeypatch.setenv("PG_ASYNC_DSN", sync_url.replace("+psycopg", ""))
    monkeypatch.setattr(settings, "DATABASE_URL", sync_url, raising=False)


def _configured_alembic_config(database_url: str) -> Config:
    cfg = Config("services/api/alembic.ini")
    cfg.set_main_option("sqlalchemy.url", database_url)
    cfg.set_main_option("script_location", "services/api/migrations")
    return cfg


def _capture_history(cfg: Config) -> str:
    buffer = io.StringIO()
    original_printer = cfg.print_stdout
    cfg.print_stdout = buffer.write  # type: ignore[assignment]
    try:
        command.history(cfg, verbose=True)
    finally:
        cfg.print_stdout = original_printer
    return buffer.getvalue()


def _current_db_revision(database_url: str) -> str:
    engine = create_engine(database_url)
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            if not version:
                raise AssertionError("alembic_version table is empty")
            return str(version)
    finally:
        engine.dispose()


def _base_sync_url() -> URL:
    raw = (os.getenv("DATABASE_URL") or "").strip()
    if raw:
        return make_url(raw)
    return make_url(build_dsn(sync=True))
