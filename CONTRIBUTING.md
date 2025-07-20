# Contributing

Install pre-commit hooks to run linting and typing checks automatically. After cloning run:

```bash
pip install pre-commit
pre-commit install
```

Before pushing changes, run all checks:

```bash
pre-commit run --all-files && pytest -q --cov
```

Run the full test suite with Postgres:

```bash
docker compose -f docker-compose.yml -f docker-compose.postgres.yml \
  --env-file .env.postgres up -d --wait
pytest -q --cov
```
