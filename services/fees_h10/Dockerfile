# syntax=docker/dockerfile:1.6
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1
WORKDIR /app
# Install dependencies first to leverage Docker layer caching.  The service
# sources live under /app/fees_h10 in the final image so that Python can
# import the `fees_h10` package.
COPY requirements*.txt constraints.txt ./fees_h10/
ARG CONSTRAINTS=""
RUN if [ -n "$CONSTRAINTS" ] && [ -f "fees_h10/$CONSTRAINTS" ]; then \
        pip install -r fees_h10/requirements.txt -c fees_h10/$CONSTRAINTS; \
    else \
        pip install -r fees_h10/requirements.txt; \
    fi
# Copy the application code into a package directory and place the start
# script at the image root.
COPY . ./fees_h10
COPY start.sh ./start.sh

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=base /usr/local /usr/local
COPY --from=base /app /app
RUN chmod +x ./start.sh
ENTRYPOINT ["./start.sh"]
HEALTHCHECK CMD ["celery", "--help"]
