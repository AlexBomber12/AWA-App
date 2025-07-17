# syntax=docker/dockerfile:1.6
FROM python:3.11-slim AS base
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt 
RUN if [ -f requirements-dev.txt ]; then pip install --no-cache-dir -r requirements-dev.txt ; fi
COPY . .

FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=base /usr/local /usr/local
COPY --from=base /app /app
CMD ["python", "-m", "logistics_etl"]
HEALTHCHECK CMD curl -fs http://localhost:8000/health || exit 1
