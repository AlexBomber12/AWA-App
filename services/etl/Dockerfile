# syntax=docker/dockerfile:1.6
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY services/etl/requirements*.txt services/etl/constraints.txt ./
ARG CONSTRAINTS=""
RUN if [ -n "$CONSTRAINTS" ] && [ -f "$CONSTRAINTS" ]; then \
        pip install -r requirements.txt -c "$CONSTRAINTS"; \
    else \
        pip install -r requirements.txt; \
    fi
COPY services/etl/ .

FROM python:3.12-slim
ARG TZ_CACHE_BUST
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=base /usr/local /usr/local
COPY --from=base /app /app
ARG DEBIAN_FRONTEND=noninteractive
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*
ENV TZ=UTC
COPY services/etl/wait-for-it.sh /usr/local/bin/wait-for-it.sh
RUN chmod +x /usr/local/bin/wait-for-it.sh
COPY services/etl/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
HEALTHCHECK CMD ["true"]
