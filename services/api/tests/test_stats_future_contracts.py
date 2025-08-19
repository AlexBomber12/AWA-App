import base64
import os
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.future


@contextmanager
def client_with_auth():
    os.environ["API_BASIC_USER"] = "u"
    os.environ["API_BASIC_PASS"] = "p"
    from services.api.main import app

    with TestClient(app) as client:
        yield client, ("u", "p")


def _auth_headers(u, p):
    return {"Authorization": f"Basic {base64.b64encode(f'{u}:{p}'.encode()).decode()}"}


def test_stats_contracts_stable_shapes():
    with client_with_auth() as (c, up):
        for path in ("/stats/kpi", "/stats/roi_by_vendor", "/stats/roi_trend"):
            r = c.get(path, headers=_auth_headers(*up))
            assert r.status_code == 200
