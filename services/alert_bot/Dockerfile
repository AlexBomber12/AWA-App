FROM --platform=$BUILDPLATFORM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt constraints.txt ./
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY alert_bot.py .
CMD ["python", "alert_bot.py"]
HEALTHCHECK CMD curl -fs http://localhost:8000/health || exit 1
