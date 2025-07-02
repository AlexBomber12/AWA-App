# AWA App

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
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=pass
export POSTGRES_DB=postgres
export POSTGRES_HOST=postgres
export POSTGRES_PORT=5432
export PG_DSN="postgresql://postgres:pass@postgres:5432/postgres"
```

All connection helpers fall back to these defaults, ensuring we never
attempt to connect using the `root` role.

