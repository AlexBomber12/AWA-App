# syntax=docker/dockerfile:1.6
FROM python:3.11-slim AS base
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements*.txt ./
ARG USE_CONSTRAINTS=false
RUN if [ "$USE_CONSTRAINTS" = "true" ] && [ -f constraints.txt ]; then \
        pip install -r requirements.txt -c constraints.txt; \
    else \
        pip install -r requirements.txt; \
    fi && \
    if [ -f requirements-dev.txt ]; then \
        if [ "$USE_CONSTRAINTS" = "true" ] && [ -f constraints.txt ]; then \
            pip install -r requirements-dev.txt -c constraints.txt; \
        else \
            pip install -r requirements-dev.txt; \
        fi; \
    fi
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
