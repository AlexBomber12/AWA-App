FROM python:3.11-slim
WORKDIR /app
COPY packages ./packages
COPY services/worker ./services/worker
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir pydantic-settings fastapi uvicorn[standard] celery redis
RUN pip install -e ./packages/awa_common
EXPOSE 8001
CMD sh -lc "celery -A services.worker.celery_app worker -l INFO & \
            celery -A services.worker.celery_app beat -l INFO & \
            uvicorn services.worker.ready:app --host 0.0.0.0 --port 8001"
