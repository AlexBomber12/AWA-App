FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY alert_bot.py .
CMD ["python","alert_bot.py"]
HEALTHCHECK CMD curl -fs http://localhost:8000/health || exit 1
