FROM python:3.11-slim AS builder
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY services/etl/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"
COPY --from=builder /opt/venv /opt/venv
COPY services/etl/wait-for-it.sh /app/wait-for-it.sh
COPY services/etl/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/wait-for-it.sh /app/entrypoint.sh
COPY services/etl /app
COPY keepa_ingestor.py services/etl/helium_fees_ingestor.py /app/
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
