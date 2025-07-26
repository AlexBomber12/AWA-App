# syntax=docker/dockerfile:1.6
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements*.txt constraints.txt ./
ARG CONSTRAINTS=""
RUN if [ -n "$CONSTRAINTS" ] && [ -f "$CONSTRAINTS" ]; then \
        pip install -r requirements.txt -c "$CONSTRAINTS"; \
    else \
        pip install -r requirements.txt; \
    fi
COPY . .

FROM python:3.12-slim
ARG TZ_CACHE_BUST
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=base /usr/local /usr/local
COPY --from=base /app /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && cp /usr/share/zoneinfo/UTC /etc/localtime \
    && echo "UTC" > /etc/timezone \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
ENV TZ=UTC
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]
HEALTHCHECK CMD curl -fs http://localhost:8100/health || exit 1
