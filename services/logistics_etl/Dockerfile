# syntax=docker/dockerfile:1.6
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY constraints.txt ./constraints.txt
ENV PIP_CONSTRAINT=/app/constraints.txt
COPY services/logistics_etl/requirements.txt ./services/logistics_etl/requirements.txt
RUN pip install -r services/logistics_etl/requirements.txt
COPY services ./services
COPY packages ./packages
COPY services/logistics_etl ./logistics_etl

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=base /usr/local /usr/local
COPY --from=base /app /app
CMD ["python", "-m", "logistics_etl"]
HEALTHCHECK CMD ["true"]
