from __future__ import annotations

from fastapi import FastAPI

from services.api import security
from services.api.routes import ingest, sku


def _route_dependency_calls(app: FastAPI, path: str, method: str) -> set[object]:
    for route in app.routes:
        if getattr(route, "path", None) == path and method in getattr(route, "methods", set()):
            return {dep.call for dep in route.dependant.dependencies}
    raise AssertionError(f"route {method} {path} not found")


def test_sku_route_uses_viewer_limiter():
    app = FastAPI()
    app.include_router(sku.router)
    calls = _route_dependency_calls(app, "/sku/{asin}", "GET")
    assert security.limit_viewer in calls


def test_ingest_post_uses_ops_limiter():
    app = FastAPI()
    app.include_router(ingest.router)
    calls = _route_dependency_calls(app, "/ingest", "POST")
    assert security.limit_ops in calls


def test_ingest_job_lookup_uses_viewer_limiter():
    app = FastAPI()
    app.include_router(ingest.router)
    calls = _route_dependency_calls(app, "/jobs/{task_id}", "GET")
    assert security.limit_viewer in calls
