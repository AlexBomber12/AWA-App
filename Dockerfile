FROM python:3.14-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY constraints.txt ./constraints.txt
ENV PIP_CONSTRAINT=/app/constraints.txt
COPY requirements-dev.txt ./requirements-dev.txt
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy API + shared code needed for the smoke test.
COPY . .
RUN pip install --no-cache-dir -e ./packages/awa_common
WORKDIR /app/services/api
ENTRYPOINT ["/app/services/api/docker-entrypoint.sh"]
HEALTHCHECK --interval=5s --timeout=2s --retries=30 CMD curl -fsS http://localhost:8000/ready || exit 1
