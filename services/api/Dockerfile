FROM python:3.11-slim
WORKDIR /app
COPY packages ./packages
COPY services/api ./services/api
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir pydantic-settings fastapi uvicorn[standard]
RUN pip install -e ./packages/awa_common
EXPOSE 8000
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
