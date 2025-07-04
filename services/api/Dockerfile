# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY services/api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY services/api /app/services/api
COPY config.py /app/config.py
COPY alembic.ini /app/alembic.ini

ENTRYPOINT ["/bin/bash", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]
