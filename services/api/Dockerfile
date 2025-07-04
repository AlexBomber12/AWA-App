# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

WORKDIR /app
# Install API dependencies
COPY services/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy wait helper
COPY services/api/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy application source
COPY services/api /app/services/api
COPY config.py /app/config.py
COPY alembic.ini /app/alembic.ini

CMD ["/entrypoint.sh"]
