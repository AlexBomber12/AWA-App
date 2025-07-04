FROM python:3.11-slim

WORKDIR /app

COPY services/etl/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY services/etl /app
COPY keepa_ingestor.py /app/

CMD ["sh", "-c", "[ \"$ENABLE_LIVE\" = '0' ] && echo 'noop' || python keepa_ingestor.py"]
