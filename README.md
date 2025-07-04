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

The ETL and API services can run against SQLite by default or Postgres. Provide
`POSTGRES_USER`, `POSTGRES_PASSWORD` and `POSTGRES_DB` in your `.env` along with
`PG_PASSWORD` for the database container. Then start the Postgres profile:

```bash
export PG_PASSWORD=pass
```

SQLite remains the default for local development. To run with Postgres just run:

```bash
docker compose -f docker-compose.yml -f docker-compose.postgres.yml up -d --wait
```

Then visit `http://localhost:8000/health` which should return `{"db": "ok"}`.

