# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"
COPY --from=builder /opt/venv /opt/venv
COPY . /tmp/api
RUN mkdir -p /app/services/api \
    && mv /tmp/api/*.py /app/services/api/ \
    && mv /tmp/api/migrations /app/migrations \
    && mv /tmp/api/templates /app/templates \
    && mv /tmp/api/config.py /app/config.py \
    && mv /tmp/api/alembic.ini /app/alembic.ini \
    && mv /tmp/api/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
HEALTHCHECK CMD curl -fs http://localhost:8000/health || exit 1
