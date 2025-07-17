# syntax=docker/dockerfile:1.6
FROM python:3.11-slim AS base
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements*.txt ./
COPY ../../constraints.txt ./
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt && if [ -f requirements-dev.txt ]; then pip install --no-cache-dir -r requirements-dev.txt -c constraints.txt; fi
COPY . .

FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=base /usr/local /usr/local
COPY --from=base /app /app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]
HEALTHCHECK CMD curl -fs http://localhost:8000/health || exit 1
