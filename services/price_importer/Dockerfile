FROM python:3.11-slim AS builder
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
# install python deps for the importer
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"
COPY --from=builder /opt/venv /opt/venv
# copy only the modules the importer relies on
COPY services_common /app/services/common
COPY . /app/price_importer
HEALTHCHECK CMD curl -fs http://localhost:8000/health || exit 1
