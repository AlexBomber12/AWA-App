# syntax=docker/dockerfile:1.6
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1
WORKDIR /app

FROM base AS deps
COPY requirements*.txt constraints.txt ./
ARG CONSTRAINTS=""
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ -n "$CONSTRAINTS" ] && [ -f "$CONSTRAINTS" ]; then \
        pip install -r requirements.txt -c "$CONSTRAINTS"; \
    else \
        pip install -r requirements.txt; \
    fi

FROM base AS runtime
COPY --from=deps /usr/local /usr/local
COPY . .
COPY start.sh ./start.sh
RUN chmod +x ./start.sh
ENTRYPOINT ["./start.sh"]
HEALTHCHECK CMD curl -fsSL http://localhost:8001/health || exit 1
