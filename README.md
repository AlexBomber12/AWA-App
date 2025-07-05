# AWA App

## Quick Start
Repricer API → http://localhost:8100/health

## Development setup

### Code style
```bash
pip install pre-commit
pre-commit install
```
Black auto-formats every commit; CI enforces `git diff --exit-code`.

### Database configuration

The ETL and API services read Postgres credentials from environment variables.
Copy `.env.example` to `.env.postgres` and spin up the stack:

```bash
cp .env.example .env.postgres
docker compose up -d --wait
curl http://localhost:8000/health
```

SQLite remains the default for local development; using the `.env.postgres`
file enables the Postgres services for API and ETL.

### Continuous Integration

The GitHub Actions test workflow uses a Postgres service container. It waits
for the database to become healthy, runs Alembic migrations and executes the
tests. No `docker compose` commands are required in CI.

