import site
import sys
from decimal import Decimal

import pytest

respx = pytest.importorskip("respx")
pytestmark = pytest.mark.usefixtures("respx_mock")

# ensure real fastapi package is used
site_pkg = site.getsitepackages()[0]
if sys.path[0] != site_pkg:
    sys.path.insert(0, site_pkg)
sys.modules.pop("fastapi", None)

from fastapi.testclient import TestClient  # noqa: E402

from services.worker.repricer.app.logic import compute_price  # noqa: E402
from services.worker.repricer.app.main import app  # noqa: E402

client = TestClient(app)  # type: ignore[arg-type]


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_compute_price():
    p = compute_price("B000TEST01", Decimal("10"), Decimal("2"))
    assert p >= Decimal("12")
