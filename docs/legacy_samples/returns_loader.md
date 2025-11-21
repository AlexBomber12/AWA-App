# Legacy returns loader

The former `services/returns_etl/loader.py` CLI truncated `returns_raw` and used
`COPY` to ingest a CSV. It is no longer shipped with the monorepo because it
skipped idempotency and clobbered the table on every run. Returns imports are now
handled by the standard ingest path:

- `python -m etl.load_csv --source path/to/returns.csv --table returns_raw`
- or via the Celery task `ingest.import_file` exposed by the API upload endpoints.

Keep this file as a reminder of the retired flow; new work should extend the shared
ingestor instead of reviving the legacy script.
