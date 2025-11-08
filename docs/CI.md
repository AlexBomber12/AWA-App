# Continuous Integration

The `CI` workflow keeps feedback fast by splitting validation into three stages:

- **prepare matrix** inspects `services/` to discover Python services and the default Python version. The job emits the service matrix that drives parallel test shards.
- **lint** runs once for the whole repo with `pre-commit`, `ruff`, and `mypy` to avoid redundant work across shards.
- **test** runs in parallel per service from the discovered matrix. Each shard installs only the dependencies declared for its service (pinning to `constraints.txt`), executes `pytest -q`, and publishes a per-service coverage XML artifact.
- **migrations** executes a full Alembic round-trip (`upgrade → downgrade → upgrade`) against a PostgreSQL 16 service using `services/api/alembic.ini`, ensuring irreversible migrations are caught early.

All jobs inherit BuildKit defaults (`DOCKER_BUILDKIT=1`, `COMPOSE_DOCKER_CLI_BUILD=1`) and use `actions/setup-python@v5` with pip caching keyed on `constraints.txt` plus each service's `requirements*.txt`. Caching keeps dependency installs fast while still respecting the global constraints lockfile.

Every job produces a `debug-bundle-<job>.tar.gz` artifact even on success. The bundle captures:

- `python --version` and `pip freeze` for the executed environment
- Docker state (`docker ps`, `docker compose ps/logs`) when available
- Alembic state via `alembic current -v` and recent history
- HTTP dumps of `http://localhost:8000/ready` and `/metrics` when reachable
- Collected CI log files from the workspace

Download the bundle from the workflow run page, extract it locally, and inspect the captured commands (each file includes the executed command and exit code). This consistent artifact makes reproducing failures offline straightforward, even when a job fails before emitting normal logs.

## Docs deployment

MkDocs builds now run in `.github/workflows/docs.yml` with a strict build, Pages artifact upload, and a gated deploy job that only runs on `main` pushes and manual dispatches. After merging updates to this workflow, open the repository **Settings -> Pages -> Build and deployment** panel and set **Source** to **GitHub Actions** so GitHub Pages is allowed to serve the published artifact (GitHub only requires the toggle once per repository).
