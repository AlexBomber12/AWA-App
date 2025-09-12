# CI debugging

The `ci` workflow uploads a debug bundle for each job. Each bundle
includes system context, docker compose logs and test output.

Artifacts:
- `debug-bundle-unit.tar.gz`
- `debug-bundle-integration.tar.gz`
- `debug-bundle-migrations.tar.gz`
- `debug-bundle-preview.tar.gz`

Sanitized copies of these bundles are pushed to the `ci-logs` branch so
that failures can be reviewed without access to the workflow run. For a
pull request use the path `ci-logs/mirror-logs/pr-<PR>/latest`. For
pushes to `main` the logs are mirrored under
`ci-logs/mirror-logs/branch-main/latest`.

## Reproducing locally

Run tests and gather a bundle:

```bash
./scripts/ci/make_debug_bundle.sh
```

The script collects test logs (`unit.log`, `integ.log`, `vitest.log`,
`tsc.log`, `eslint.log`), docker compose output, git status and Alembic
history, then writes `debug-bundle.tar.gz` in the current directory.
