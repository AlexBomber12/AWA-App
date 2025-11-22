from services.worker import ready


def test_worker_probe_app_exposes_no_ingest_routes():
    paths = {route.path for route in ready.app.routes}
    assert "/ingest" not in paths
    assert not any(path.startswith("/ingest") for path in paths)
