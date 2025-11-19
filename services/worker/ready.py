import redis
from fastapi import FastAPI, status

from awa_common.settings import settings

# If Celery app is available:
try:
    from services.worker.celery_app import celery_app
except Exception:  # pragma: no cover - celery optional
    celery_app = None

app = FastAPI(title="AWA Worker Probe")


@app.get("/ready")
async def ready():
    # 1) broker connectivity
    try:
        timeout = float(getattr(settings, "HEALTHCHECK_REDIS_SOCKET_TIMEOUT_S", 2.0))
        r = redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=timeout,
            socket_timeout=timeout,
        )
        r.ping()
    except Exception:
        return {
            "status": "fail",
            "reason": "redis",
        }, status.HTTP_503_SERVICE_UNAVAILABLE
    # 2) celery ping (best-effort)
    if celery_app:
        try:
            inspect_timeout = float(getattr(settings, "HEALTHCHECK_INSPECT_TIMEOUT_S", 1.0))
            i = celery_app.control.inspect(timeout=inspect_timeout)
            pong = i.ping() or {}
            if not pong:
                return {
                    "status": "fail",
                    "reason": "celery-ping",
                }, status.HTTP_503_SERVICE_UNAVAILABLE
        except Exception:
            return {
                "status": "fail",
                "reason": "celery-exc",
            }, status.HTTP_503_SERVICE_UNAVAILABLE
    app_env = getattr(getattr(settings, "app", None), "env", getattr(settings, "ENV", "local"))
    return {"status": "ok", "env": app_env}
