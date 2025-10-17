FROM python:3.14-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements*.txt constraints.txt ./
ARG CONSTRAINTS=""
RUN if [ -n "$CONSTRAINTS" ] && [ -f "$CONSTRAINTS" ]; then \
        pip install --no-cache-dir -r requirements.txt -c "$CONSTRAINTS"; \
    else \
        pip install --no-cache-dir -r requirements.txt; \
    fi
COPY . .
ENTRYPOINT ["python", "keepa_ingestor.py"]
HEALTHCHECK CMD ["true"]
