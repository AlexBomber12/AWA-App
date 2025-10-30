FROM python:3.14-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY constraints.txt ./constraints.txt
ENV PIP_CONSTRAINT=/app/constraints.txt
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENTRYPOINT ["python", "-m", "services.etl.keepa_ingestor"]
HEALTHCHECK CMD ["true"]
