FROM python:3.11-slim

WORKDIR /app

COPY services/etl/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/etl/wait-for-it.sh /app/wait-for-it.sh
COPY services/etl/entrypoint.sh /app/entrypoint.sh
COPY services/etl /app
COPY keepa_ingestor.py /app/
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
