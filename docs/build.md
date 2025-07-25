# Build Guide

## Docker images

### API

`alembic.ini` is copied into the API image at `/app/services/api/alembic.ini` solely for CI inspection.

CI uploads coverage using the `codecov-action` workflow step. Define `CODECOV_TOKEN` in the repository secrets to enable reporting; otherwise the upload step is skipped.
