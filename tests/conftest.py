import os
import subprocess
import pytest
import site
import sys

import time

os.environ.setdefault("ENABLE_LIVE", "0")
from services.common.settings import settings

os.makedirs("/data", exist_ok=True)
os.makedirs("data", exist_ok=True)

# ensure real fastapi package is used
site_pkg = site.getsitepackages()[0]
if sys.path[0] != site_pkg:
    sys.path.insert(0, site_pkg)
sys.modules.pop("fastapi", None)
from fastapi.testclient import TestClient  # noqa: E402
from services.api.main import app  # noqa: E402


def _wait_for_db() -> None:
    if settings.DATABASE_URL.startswith("sqlite"):
        return
    for _ in range(10):
        try:
            rc = subprocess.run(
                [
                    "pg_isready",
                    "-h",
                    settings.PG_HOST,
                    "-p",
                    str(settings.PG_PORT),
                    "-U",
                    settings.PG_USER,
                ],
                capture_output=True,
            ).returncode
        except FileNotFoundError:
            return
        if rc == 0:
            return
        time.sleep(1)
    raise RuntimeError("postgres not ready")


def pytest_sessionstart(session):
    _wait_for_db()
    url = settings.DATABASE_URL
    if url.startswith("sqlite"):
        path = url.split("///", 1)[1]
        if os.path.exists(path):
            os.remove(path)
    subprocess.run(
        ["alembic", "upgrade", "head"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


@pytest.fixture
def api_client() -> TestClient:
    return TestClient(app)
