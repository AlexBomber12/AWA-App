from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from fastapi import APIRouter, FastAPI, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

requests_total = Counter(
    "requests_total",
    "HTTP request count",
    ("method", "route", "status"),
)
request_duration_seconds = Histogram(
    "request_duration_seconds",
    "HTTP request duration",
    ("method", "route"),
    buckets=(0.025, 0.05, 0.1, 0.2, 0.3, 0.5, 1, 2, 5),
)
inprogress_requests = Gauge(
    "inprogress_requests",
    "In-flight requests",
)

_router = APIRouter()


@_router.get("/metrics", include_in_schema=False)
async def metrics_endpoint() -> Response:
    # Collect and return the latest Prometheus metrics snapshot.
    payload = generate_latest()
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)


def _route_template(request: Request) -> str:
    route: Any = request.scope.get("route")
    if route is not None:
        path_format = getattr(route, "path_format", None)
        if isinstance(path_format, str):
            return path_format
        path = getattr(route, "path", None)
        if isinstance(path, str):
            return path
    return request.url.path


def install_metrics(app: FastAPI) -> None:
    app.include_router(_router)

    @app.middleware("http")
    async def _metrics_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        method = request.method.upper()
        route = _route_template(request)
        start_time = time.monotonic()
        status_code: int | None = None
        with inprogress_requests.track_inprogress():
            try:
                response = await call_next(request)
                status_code = response.status_code
                return response
            except HTTPException as exc:
                status_code = exc.status_code
                raise
            except Exception:
                status_code = 500
                raise
            finally:
                elapsed = time.monotonic() - start_time
                labels = {"method": method, "route": route}
                status_value = str(status_code or 500)
                requests_total.labels(**labels, status=status_value).inc()
                request_duration_seconds.labels(**labels).observe(elapsed)


__all__ = [
    "install_metrics",
    "inprogress_requests",
    "request_duration_seconds",
    "requests_total",
]
