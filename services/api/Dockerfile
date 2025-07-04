# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

WORKDIR /app
# Install API dependencies
COPY services/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint
COPY services/api/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Copy application source
COPY services/api /app/services/api
COPY config.py /app/config.py
COPY alembic.ini /app/alembic.ini

CMD ["/docker-entrypoint.sh"]
