FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY constraints.txt ./constraints.txt
ENV PIP_CONSTRAINT=/app/constraints.txt
COPY services/api/requirements.txt ./services/api/requirements.txt
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r services/api/requirements.txt
COPY packages ./packages
COPY services/api ./services/api
RUN pip install --no-cache-dir -e ./packages/awa_common
WORKDIR /app/services/api
RUN chmod +x docker-entrypoint.sh
EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
HEALTHCHECK --interval=5s --timeout=2s --retries=30 CMD curl -fsS http://localhost:8000/ready || exit 1
