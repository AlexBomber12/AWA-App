# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../../scripts/wait_for_db.py /wait_for_db.py

COPY . .
CMD ["python", "/wait_for_db.py", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
