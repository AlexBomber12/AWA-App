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
Copy `.env.postgres` to `.env` to provide `PG_USER`, `PG_PASSWORD`, `PG_HOST`,
`PG_PORT` and `PG_DATABASE`:

```bash
cp .env.postgres .env
```

SQLite remains the default for local development. To run with Postgres just run:

```bash
docker compose --env-file .env.postgres -f docker-compose.yml -f docker-compose.postgres.yml up -d --wait
```

Then visit `http://localhost:8000/health` which should return `{"db": "ok"}`.

