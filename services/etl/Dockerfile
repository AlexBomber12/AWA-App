FROM python:3.11-slim

WORKDIR /app

COPY services/etl/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/wait_db.sh /app/wait_db.sh
COPY services/etl/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/wait_db.sh /app/entrypoint.sh
COPY services/etl /app
COPY keepa_ingestor.py services/etl/helium_fees_ingestor.py /app/
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
