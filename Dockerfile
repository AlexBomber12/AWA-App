FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENTRYPOINT ["python", "keepa_ingestor.py"]
HEALTHCHECK CMD curl -fs http://localhost:8000/health || exit 1
