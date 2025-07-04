import os
import subprocess
import pytest
import site
import sys

# ensure real fastapi package is used
site_pkg = site.getsitepackages()[0]
if sys.path[0] != site_pkg:
    sys.path.insert(0, site_pkg)
sys.modules.pop("fastapi", None)
from fastapi.testclient import TestClient  # noqa: E402
from services.api.main import app  # noqa: E402


def pytest_sessionstart(session):
    if not os.getenv("DATABASE_URL") and os.path.exists(".env.postgres"):
        with open(".env.postgres") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ.setdefault(k, v)
    if os.getenv("DATABASE_URL"):
        try:
            subprocess.run(["alembic", "upgrade", "head"], check=True)
        except Exception:
            pass


@pytest.fixture
def api_client() -> TestClient:
    return TestClient(app)
