# syntax=docker/dockerfile:1.6
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY constraints.txt ./constraints.txt
ENV PIP_CONSTRAINT=/app/constraints.txt
COPY services/price_importer/requirements.txt ./services/price_importer/requirements.txt
RUN pip install -r services/price_importer/requirements.txt
COPY . .

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=base /usr/local /usr/local
COPY --from=base /app /app
CMD ["python", "-m", "price_importer.import"]
HEALTHCHECK CMD ["true"]
