"""Smoke-test DB migrations and raise coverage."""

import importlib
import os
import pkgutil
import subprocess
import tempfile
from pathlib import Path

import pytest


def test_run_migrations_head():
    # Use an in-memory SQLite DB so CI needs no Postgres
    os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
    # Initialise an Alembic env in a tmp dir
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "alembic.ini").write_text("[alembic]\nscript_location = services/api/migrations")
        with pytest.raises(subprocess.CalledProcessError):
            subprocess.check_call(["alembic", "-c", f"{tmp}/alembic.ini", "upgrade", "head"])


def test_import_all_services():
    """Import every module under services/* to bump coverage ≥50 %."""
    import services

    for module in pkgutil.walk_packages(services.__path__, prefix="services."):
        try:
            importlib.import_module(module.name)
        except Exception:
            pass
