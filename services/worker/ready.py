import redis
from awa_common.settings import settings
from fastapi import FastAPI, status

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
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
    except Exception:
        return {
            "status": "fail",
            "reason": "redis",
        }, status.HTTP_503_SERVICE_UNAVAILABLE
    # 2) celery ping (best-effort)
    if celery_app:
        try:
            i = celery_app.control.inspect(timeout=1)
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
    return {"status": "ok", "env": settings.ENV}
