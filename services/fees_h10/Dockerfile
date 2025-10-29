# syntax=docker/dockerfile:1.6
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1
WORKDIR /app
# Install dependencies first to leverage Docker layer caching.  The service
# sources live under /app/fees_h10 in the final image so that Python can
# import the `fees_h10` package.
COPY constraints.txt ./constraints.txt
ENV PIP_CONSTRAINT=/app/constraints.txt
COPY services/fees_h10/requirements.txt ./fees_h10/requirements.txt
RUN pip install -r fees_h10/requirements.txt
# Copy the application code into a package directory and place the start
# script at the image root.
COPY services ./services
COPY packages ./packages
COPY services/fees_h10 ./fees_h10
COPY services/fees_h10/start.sh ./start.sh

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=base /usr/local /usr/local
COPY --from=base /app /app
RUN chmod +x ./start.sh
ENTRYPOINT ["./start.sh"]
HEALTHCHECK CMD ["celery", "--help"]
