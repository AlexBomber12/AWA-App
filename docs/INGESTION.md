# Ingestion pipeline

The FastAPI `/ingest` route is the canonical entry point for uploads. The legacy `/upload` path
still proxies to the same codepath for compatibility but should be treated as deprecated in docs and
UI links. Both routes validate payloads, emit consistent error responses, and enqueue the Celery
`ingest.import_file` task.

## Supported flows

- **Direct upload** — `POST /ingest` with `multipart/form-data` (`file` field). Intended for browser
  uploads and CLI helpers.
- **URI ingestion** — `POST /ingest` with `{"uri": "s3://..."}` or HTTP(S)/MinIO URIs. The API
  downloads the content, validates size and extension, and enqueues the same Celery task.
- **Streaming ingestion** — Enabled when `INGEST_STREAMING_ENABLED=1` and the resolved payload size
  exceeds `INGEST_STREAMING_THRESHOLD_MB`. The worker streams the file in chunks
  (`INGEST_STREAMING_CHUNK_SIZE` rows or `INGEST_STREAMING_CHUNK_SIZE_MB` as a size hint) instead of
  loading the full body into memory. Smaller files take the standard in-memory path.

## Error handling

Both endpoints return a structured JSON error:

```json
{
  "error": {
    "code": "unsupported_file_format",
    "message": "Only CSV/XLSX files are supported.",
    "status": 415
  },
  "requestId": "req-123"
}
```

Common cases:

- `400 bad_request` / `422 validation_error` — missing payload or schema validation failure.
- `413 payload_too_large` — exceeds `MAX_REQUEST_BYTES` (API) or `SPOOL_MAX_BYTES` during streaming.
- `415 unsupported_file_format` — extension not in the allow list.
- `502 ingest_task_failed` — Celery task raised unexpectedly (task id and request id are logged).

Metrics are emitted for every branch (`api_ingest_4xx_total{code}`, `api_ingest_5xx_total`,
`ingest_upload_bytes_total`, and `ingest_download_bytes_total{scheme}`) and `load_log` records the
payload metadata and idempotency key so streaming vs. non-streaming runs can be compared.

## Behavioural guarantees

- Streaming vs. non-streaming ingestion produce identical `load_log` metadata and table results for
  the same payload; idempotency is enforced through the shared guard (`ingest.import_file` writes
  `status='skipped'` on duplicates).
- Multipart uploads are validated before enqueueing: extension allow-list, request size, and
  optional `ingestion.report_type` overrides.
- URI downloads honour HTTP timeouts from `settings.http_client` and MinIO/S3 settings; download
  failures increment `ingest_download_failure_total{scheme}`.

## Configuration quick reference

| Variable | Purpose |
| --- | --- |
| `INGEST_STREAMING_ENABLED` | Toggle streaming ingestion in the Celery task |
| `INGEST_STREAMING_THRESHOLD_MB` | Minimum size before switching to streaming |
| `INGEST_STREAMING_CHUNK_SIZE` / `INGEST_STREAMING_CHUNK_SIZE_MB` | Chunk sizing (rows or MB hint) |
| `MAX_REQUEST_BYTES`, `SPOOL_MAX_BYTES` | API/streaming payload caps |
| `INGEST_CHUNK_SIZE_MB` | Multipart chunk size for uploads to MinIO/S3 |
| `INGEST_IDEMPOTENT` | Enable idempotency guard via `load_log` |

Use `docs/ETL.md` for the complete reliability layer and replay guidance.
