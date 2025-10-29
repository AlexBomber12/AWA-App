# syntax=docker/dockerfile:1.6
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY constraints.txt ./constraints.txt
ENV PIP_CONSTRAINT=/app/constraints.txt
COPY services/alert_bot/requirements.txt ./services/alert_bot/requirements.txt
RUN pip install -r services/alert_bot/requirements.txt
COPY . .

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=base /usr/local /usr/local
COPY --from=base /app /app
CMD ["python", "alert_bot.py"]
HEALTHCHECK CMD ["true"]
