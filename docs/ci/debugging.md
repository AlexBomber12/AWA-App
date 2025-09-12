# CI Debugging Bundle

The CI workflow uploads a `debug-bundle-*.tar.gz` artifact for each job. Each bundle contains:

- `system.txt` – redacted environment, Docker and git info
- `docker/` – `docker ps`, `docker compose ps`, and compose logs
- test output logs (`unit.log`, `integ.log`, `vitest.log`, `tsc.log`, `eslint.log`)
- `migrations/alembic.txt` – alembic status and recent history

To inspect, download and extract the archive:

```bash
tar -xzf debug-bundle.tar.gz
cat debug-bundle/system.txt
```

Compose logs and test outputs can be found in the extracted directory. Use the captured commands to reproduce failures locally.
