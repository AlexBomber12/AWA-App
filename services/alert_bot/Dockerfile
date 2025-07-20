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
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=base /usr/local /usr/local
COPY --from=base /app /app
CMD ["python", "alert_bot.py"]
HEALTHCHECK CMD ["true"]
