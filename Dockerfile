FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN if [ -f requirements-dev.txt ]; then pip install --no-cache-dir -r requirements-dev.txt; fi
COPY . .
ENTRYPOINT ["python", "keepa_ingestor.py"]
HEALTHCHECK CMD curl -fs http://localhost:8000/health || exit 1
