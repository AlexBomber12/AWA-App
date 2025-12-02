# LLM provider options

The platform now supports a strict two-provider model:

- `LLM_PROVIDER=local` (default) points to the on-prem OpenAI-compatible endpoint.
  Configure `LLM_PROVIDER_BASE_URL` and optional `LLM_API_KEY` for auth.
- `LLM_SECONDARY_PROVIDER=cloud` enables GPT-5 in the OpenAI cloud for large or
  complex requests. Set `LLM_CLOUD_API_KEY`, `LLM_CLOUD_MODEL`, and optional
  `LLM_CLOUD_API_BASE` to route traffic.

Clients always call the gateway at `LLM_BASE_URL`; the gateway handles routing
between local/cloud and validates JSON-only responses for tasks such as
`classify_email` and `parse_price_list`.

## Server behaviour and resiliency

- The server enforces request-level timeouts (`LLM_REQUEST_TIMEOUT_SEC`) and bounded retries
  (`LLM_MAX_RETRIES`, `LLM_BACKOFF_BASE_MS`, `LLM_BACKOFF_MAX_MS`). Timeout and retry classifications
  are surfaced as Prometheus counters and structured logs so flaky providers are visible.
- Provider responses are validated for JSON-only payloads; invalid or oversized results raise
  `LLMInvalidResponseError` and return a 502 to callers.
- Local binary providers (for completely offline runs) honour `LLM_BIN_TIMEOUT_SEC` and clamp stdout
  to `LLM_MAX_OUTPUT_BYTES`. `LLMBinaryTimeoutError`, `LLMBinaryNonZeroExitError`, and
  `LLMBinaryOSFailure` are mapped to HTTP 504/502 responses with a sanitized message.
- The gateway prefers the configured primary provider; when a secondary provider is configured it is
  used only when the task or payload crosses the thresholds
  (`LLM_EMAIL_CLOUD_THRESHOLD_CHARS`, `LLM_PRICELIST_CLOUD_THRESHOLD_ROWS`) or when the primary
  provider returns a retriable error.

## Configuration quick reference

| Variable | Purpose |
| --- | --- |
| `LLM_PROVIDER`, `LLM_SECONDARY_PROVIDER` | Provider order (`local`, `cloud`, or empty secondary) |
| `LLM_BASE_URL`, `LLM_PROVIDER_BASE_URL`, `LLM_CLOUD_API_BASE` | Gateway URL and downstream bases |
| `LLM_API_KEY`, `LLM_LOCAL_MODEL`, `LLM_CLOUD_MODEL`, `LLM_CLOUD_API_KEY` | Auth + model selection |
| `LLM_REQUEST_TIMEOUT_SEC`, `LLM_MAX_RETRIES`, `LLM_BACKOFF_BASE_MS`, `LLM_BACKOFF_MAX_MS` | Request timeout + retry budget |
| `LLM_BIN_TIMEOUT_SEC`, `LLM_MAX_OUTPUT_BYTES` | Local binary subprocess controls |
| `LLM_EMAIL_CLOUD_THRESHOLD_CHARS`, `LLM_PRICELIST_CLOUD_THRESHOLD_ROWS`, `LLM_MIN_CONFIDENCE` | Routing thresholds and validation guardrails |

See `docs/CONFIG.md#llm` for the complete settings table. Tests under `tests/test_llm_endpoint.py`,
`tests/test_llm_provider_client.py`, and `tests/test_llm_bin_runner.py` exercise the happy path,
timeouts, retries, and subprocess failures.
