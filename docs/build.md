# Build Guide

## Docker images

### API

`alembic.ini` is copied into the API image at `/app/services/api/alembic.ini` solely for CI inspection.

All runtime containers use the UTC timezone to avoid clock-skew issues between services.

CI uploads coverage using the `codecov-action` workflow step. Define `CODECOV_TOKEN` in the repository secrets to enable reporting; otherwise the upload step is skipped.
