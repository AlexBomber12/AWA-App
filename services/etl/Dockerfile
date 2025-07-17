# syntax=docker/dockerfile:1.6
FROM python:3.11-slim AS base
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements*.txt ./
RUN PIP_CONSTRAINTS=""; [ -f constraints.txt ] && PIP_CONSTRAINTS="-c constraints.txt"; \
    pip install --no-cache-dir -r requirements.txt $PIP_CONSTRAINTS && \
    if [ -f requirements-dev.txt ]; then pip install --no-cache-dir -r requirements-dev.txt $PIP_CONSTRAINTS; fi
COPY . .

FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=base /usr/local /usr/local
COPY --from=base /app /app
COPY wait-for-it.sh /app/wait-for-it.sh
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/wait-for-it.sh /app/entrypoint.sh
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
HEALTHCHECK CMD curl -fs http://localhost:8000/health || exit 1
