# CI debugging

Every workflow run uploads a `debug-bundle` artifact that contains logs, system
information, and migration details. Look for the bundle in the run's Artifacts
section; each job attaches its own archive.

For pull requests from the main repository the CI also posts a single digest
comment. The comment shows the preview URL, first error lines, and log tails.
Reruns update the same comment instead of adding new ones. Forked pull requests
don't receive digest comments but still publish artifacts.

To reproduce the CI environment locally:

1. Install Python 3.11 and Node 20.
2. `pip install -r requirements-dev.txt` and any service requirements.
3. Run backend tests with `pytest -vv -q -m "not integration"`.
4. For frontend work `npm ci` then `npm run lint`, `npx tsc -p .`, and
   `npm run test:unit`.
5. Integration tests use Docker Compose: `docker compose up -d db redis api
   worker` then `pytest -vv -m integration`.

Fork PRs usually lack permission to comment, so check the run summary and
artifact bundle when the digest comment is missing.
