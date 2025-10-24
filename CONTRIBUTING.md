# Contributing

Install pre-commit hooks to run linting and typing checks automatically. After cloning run:

```bash
pip install pre-commit
pre-commit install
```

For local development, copy the example environment file and start the stack:

```bash
cp .env.example .env.local
docker compose up -d --build
```

After the containers start, `/ready` should return 200 and the logs include a
redacted `settings={...}` banner. Staging and production deployments should
provide variables via the orchestrator or a secrets manager; `.env.prod.example`
documents the expected keys.

Run the full test suite:

```bash
ENV=test pytest -q
```

Coverage quickstart (matches the CI gate):

```bash
pytest -q -m "not integration" --cov=services/api --cov=services/worker --cov=packages/awa_common
```

Before pushing changes, run the full pre-commit suite and tests:

```bash
pre-commit run --all-files && pytest -q --cov
```
This ensures formatting, linting, and coverage remain consistent with CI.

### Regenerating API docs
Install `pydoc-markdown` and run it from the repo root to update the Markdown files under `docs/api`:

```bash
pip install pydoc-markdown
pydoc-markdown
```

The rendered pages are published at <https://your-org.github.io/AWA-App/> when pushed to `main`.
