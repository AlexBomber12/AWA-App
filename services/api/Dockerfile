FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY ../scripts/wait-for-postgres.sh ./wait-for-postgres.sh
RUN chmod +x wait-for-postgres.sh
CMD ["./wait-for-postgres.sh", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
