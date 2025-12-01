# Legacy ETL agents (inventory)

- **Location:** Quarantined scripts now live under `docs/legacy_samples/etl/*`; `services/etl/` only holds supported helpers (`load_csv`, `healthcheck`, dialects).
- **Active stack:** Helium10 fees runs through `services/fees_h10/*` with `awa_common.http_client.AsyncHTTPClient`; no production Celery tasks or API routes import the old ingestors.
- **Archived agents:** `keepa_ingestor.py` and the earlier `keepa_etl.py` (MinIO/etl_log), Helium10 CLI wrappers `fba_fee_ingestor.py`/`helium_fees.py`, and the SP-API helper `sp_fees.py`/`sp_fees_ingestor.py`. These were only referenced in legacy docs/tests and are kept for historical reference under `docs/legacy_samples/etl/` (run with `python -m docs.legacy_samples.etl.<module>` if needed).
- **HTTP client:** Removed `services/etl/http_client.py`; all outbound calls should flow through `awa_common.http_client` (async via `AsyncHTTPClient`).
- **Tests:** Legacy-only pytest modules exercising the ingestors were deleted to avoid pulling them back into the supported surface. Live ingestion/fees coverage remains under `tests/fees_h10/*` and other ETL suites.

Keep future examples under `docs/legacy_samples/etl/` rather than `services/etl/` to avoid reintroducing retired agents into production paths.
