import os
import subprocess
import pytest
import site
import sys

from services.common.db_url import build_db_url

os.environ.setdefault("ENABLE_LIVE", "0")

os.makedirs("/data", exist_ok=True)
os.makedirs("data", exist_ok=True)

# ensure real fastapi package is used
site_pkg = site.getsitepackages()[0]
if sys.path[0] != site_pkg:
    sys.path.insert(0, site_pkg)
sys.modules.pop("fastapi", None)
from fastapi.testclient import TestClient  # noqa: E402
from services.api.main import app  # noqa: E402


def pytest_sessionstart(session):
    url = build_db_url()
    if url.startswith("sqlite"):
        path = url.split("///", 1)[1]
        if os.path.exists(path):
            os.remove(path)
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
    except Exception:
        pass


@pytest.fixture
def api_client() -> TestClient:
    return TestClient(app)
