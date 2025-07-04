# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

WORKDIR /app
# Install API dependencies
COPY services/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy helper script for database readiness and migrations
COPY scripts/wait_for_db.py /wait_for_db.py

# Copy application source
COPY services/api .
CMD ["python", "/wait_for_db.py", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
