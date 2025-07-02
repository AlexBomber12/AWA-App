def test_health_offline() -> None:
    import os
    import sys
    import site

    # ensure real fastapi package is used
    site_pkg = site.getsitepackages()[0]
    if sys.path[0] != site_pkg:
        sys.path.insert(0, site_pkg)
    sys.modules.pop("fastapi", None)

    from services.api.main import app
    from fastapi.testclient import TestClient

    os.environ.pop("DATABASE_URL", None)
    os.environ["ENABLE_LIVE"] = "0"
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
