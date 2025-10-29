FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY constraints.txt ./constraints.txt
ENV PIP_CONSTRAINT=/app/constraints.txt
COPY services/api/requirements.txt ./services/api/requirements.txt
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r services/api/requirements.txt
COPY packages ./packages
COPY services/api ./services/api
RUN pip install --no-cache-dir -e ./packages/awa_common
EXPOSE 8000
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
