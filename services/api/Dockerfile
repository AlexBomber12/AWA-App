# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY services/api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY services/api /app/services/api
COPY services/api/migrations/ /app/migrations/
COPY config.py /app/config.py
COPY alembic.ini /app/alembic.ini
COPY scripts/wait-for-postgres.sh /app/wait-for-postgres.sh
COPY services/api/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/wait-for-postgres.sh /app/entrypoint.sh
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
