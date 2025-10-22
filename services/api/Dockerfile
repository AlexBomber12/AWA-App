FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY constraints.txt /tmp/constraints.txt
COPY services/api/requirements.txt ./services/api/requirements.txt
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r services/api/requirements.txt -c /tmp/constraints.txt
COPY packages ./packages
COPY services/api ./services/api
RUN pip install --no-cache-dir -e ./packages/awa_common -c /tmp/constraints.txt
EXPOSE 8000
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
