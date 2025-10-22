FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY constraints.txt ./constraints.txt
COPY services/worker/requirements.txt ./services/worker/requirements.txt
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r services/worker/requirements.txt -c constraints.txt
COPY packages ./packages
COPY services/worker ./services/worker
RUN pip install --no-cache-dir -e ./packages/awa_common -c constraints.txt
EXPOSE 8001
CMD sh -lc "celery -A services.worker.celery_app worker -l INFO & \
            celery -A services.worker.celery_app beat -l INFO & \
            uvicorn services.worker.ready:app --host 0.0.0.0 --port 8001"
