FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY constraints.txt ./constraints.txt
ENV PIP_CONSTRAINT=/app/constraints.txt
COPY requirements-dev.txt ./requirements-dev.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy API + shared code needed for the smoke test.
COPY packages ./packages
COPY services/api ./services/api
COPY services/etl ./services/etl
COPY scripts ./scripts
COPY pyproject.toml ./pyproject.toml
COPY constraints.txt ./constraints.txt

# Install repo package in editable mode so imports resolve.
RUN pip install --no-cache-dir -e ./packages/awa_common

WORKDIR /app/services/api
ENTRYPOINT ["/app/services/api/docker-entrypoint.sh"]
HEALTHCHECK --interval=5s --timeout=2s --retries=30 CMD curl -fsS http://localhost:8000/ready || exit 1
