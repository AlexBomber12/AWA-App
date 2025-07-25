# Build

## Docker images

### API
The API Dockerfile copies `services/api/alembic.ini` into the image so tests can confirm the migration config is present.
