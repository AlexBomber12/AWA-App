FROM python:3.11-slim AS builder
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
# install python deps for the importer
COPY services/price_importer/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"
COPY --from=builder /opt/venv /opt/venv
# copy only the modules the importer relies on
COPY services/common /app/services/common
COPY services/price_importer /app/price_importer
HEALTHCHECK CMD curl -fs http://localhost:8000/health || exit 1
