FROM python:3.11-slim AS builder
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"
COPY --from=builder /opt/venv /opt/venv
COPY . /app/services/fees_h10
CMD ["celery", "-A", "services.fees_h10.worker", "beat", "-l", "info"]
HEALTHCHECK CMD curl -fs http://localhost:8000/health || exit 1
