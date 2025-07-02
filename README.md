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

The ETL and API services expect a Postgres instance configured via
environment variables. A typical local setup might use:

```bash
export DATABASE_URL="postgresql+asyncpg://awa:awa@postgres:5432/awa"
```


SQLite remains the default for local development. To run with Postgres just run:

```bash
docker compose -f docker-compose.yml -f docker-compose.postgres.yml up -d --wait
```

Then visit `http://localhost:8000/health`.

