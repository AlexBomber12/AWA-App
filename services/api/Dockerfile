FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends bash curl postgresql-client && rm -rf /var/lib/apt/lists/*
COPY constraints.txt ./constraints.txt
ENV PIP_CONSTRAINT=/app/constraints.txt
COPY services/api/requirements.txt ./services/api/requirements.txt
COPY services/etl/requirements.txt ./services/etl/requirements.txt
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r services/api/requirements.txt -r services/etl/requirements.txt
COPY packages ./packages
COPY services/api ./services/api
COPY services/etl ./services/etl
RUN pip install --no-cache-dir -e ./packages/awa_common
COPY services/api/docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh
ENTRYPOINT ["/app/docker-entrypoint.sh"]
WORKDIR /app/services/api
EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=2s --retries=30 CMD curl -fsS http://localhost:8000/ready || exit 1
