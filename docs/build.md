# Build Guide

## Docker images

### API

`alembic.ini` is copied into the API image at `/app/services/api/alembic.ini` solely for CI inspection.

All runtime containers use the UTC timezone to avoid clock-skew issues between services.

The API entrypoint seeds default Postgres settings before enabling strict mode so that
`docker run services/api` can start without additional environment variables. When no
CLI arguments are provided the script waits for Postgres, applies Alembic migrations,
and execs the default `uvicorn` command (override via `DEFAULT_API_CMD`). If arguments
are supplied they are executed directly without running migrations; this behaviour is
required by the test suite.

CI uploads coverage using the `codecov-action` workflow step. Define `CODECOV_TOKEN` in the repository secrets to enable reporting; otherwise the upload step is skipped.
