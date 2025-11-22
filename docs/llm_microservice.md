# LLM Microservice

The LLM gateway routes structured, JSON-only tasks to two providers:

- **local** — on-prem OpenAI-compatible endpoint (DGX-like host) for day-to-day work.
- **cloud** — GPT-5 in the OpenAI cloud for large or complex inputs.

Requests are strongly typed: callers include a `task` plus the expected schema, and the service
validates/returns only JSON that matches that schema.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r services/llm_server/requirements.txt
uvicorn services.llm_server.app:app --host 0.0.0.0 --port 8001
```

## Configuration
| Variable | Purpose | Default |
| -------- | ------- | ------- |
| `LLM_PROVIDER` | Default provider (`local` or `cloud`). | `local` |
| `LLM_SECONDARY_PROVIDER` | Optional fallback provider. | _empty_ |
| `LLM_BASE_URL` | Public gateway URL clients call (`http://localhost:8001`). | `http://localhost:8000` |
| `LLM_PROVIDER_BASE_URL` | Downstream local provider base (OpenAI-compatible). | _empty_ |
| `LLM_API_KEY` | Shared secret for the local provider. | _empty_ |
| `LLM_LOCAL_MODEL`, `LLM_CLOUD_MODEL` | Model names for local and cloud calls. | `gpt-4o-mini` / `gpt-5` |
| `LLM_CLOUD_API_KEY`, `LLM_CLOUD_API_BASE` | Cloud GPT-5 credentials + optional base URL override. | _empty_ |
| `LLM_REQUEST_TIMEOUT_S` | Request timeout for both providers. | `60` |
| `LLM_EMAIL_CLOUD_THRESHOLD_CHARS`, `LLM_PRICELIST_CLOUD_THRESHOLD_ROWS` | Thresholds that trigger cloud routing. | `12000`, `500` |
| `LLM_ENABLE_EMAIL`, `LLM_ENABLE_PRICELIST` | Feature flags for email/price list enrichment. | `0` |
| `LLM_MIN_CONFIDENCE` | Minimum confidence before responses are marked invalid. | `0.35` |

## API surface
- `GET /health` / `GET /ready` — readiness probes.
- `POST /llm` — accepts JSON:
  ```json
  {
    "task": "classify_email" | "parse_price_list" | "chat_completion",
    "provider": "local",
    "model": "gpt-4o-mini",
    "temperature": 0.0,
    "max_tokens": 800,
    "schema": { "...": "json schema (optional)" },
    "input": { "...": "task-specific payload" }
  }
  ```
  Responses are always JSON: `{"task":"classify_email","provider":"local","result":{...}}`.

### Examples
- Email classification request/response:
  ```json
  {
    "task": "classify_email",
    "provider": "local",
    "input": {
      "subject": "Price list request",
      "body": "Please share FOB USD...",
      "sender": "buyer@example.com",
      "has_price_list_attachment": false
    }
  }
  ```
  ```json
  {
    "task": "classify_email",
    "provider": "local",
    "result": {
      "intent": "price_list",
      "facts": { "currency": "USD", "incoterms": "FOB" },
      "confidence": 0.91
    }
  }
  ```
- Price list parsing request/response:
  ```json
  {
    "task": "parse_price_list",
    "input": {
      "headers": ["SKU","Price","Currency"],
      "rows": [["A1","12.50","USD"]],
      "vendor_id": 10,
      "file_name": "prices.csv"
    }
  }
  ```
  ```json
  {
    "task": "parse_price_list",
    "provider": "cloud",
    "result": {
      "detected_columns": {"sku": "SKU", "cost": "Price", "currency": "Currency"},
      "column_confidence": {"sku": 0.99, "cost": 0.94},
      "needs_review": false
    }
  }
  ```

## Provider routing & safety
- Providers are validated at startup; unknown values fail fast.
- Local is the default; cloud is used when requested explicitly or when size thresholds are exceeded.
- Fallback to cloud is logged via `llm_fallback_total` and never silent.
- Responses are parsed as JSON and validated against Pydantic models (`EmailLLMResult`, `PriceListLLMResult`);
  invalid JSON yields HTTP 502 without leaking prompts or API keys.

## Observability
- Metrics: `llm_requests_total`, `llm_request_latency_seconds`, `llm_request_errors_total`,
  `llm_fallback_total` with labels `{task,provider,...}`.
- HTTP middleware exposes `/metrics`; forward to Prometheus/Grafana alongside other services.
- Logs include `task`, `provider`, and `error_type` but omit bodies/keys to avoid PII/secrets.

## Client usage
- Use `awa_common.llm.LLMClient` helpers:
  - `await classify_email(subject, body, sender, has_price_list_attachment=...)`
  - `await parse_price_list(preview=..., row_count=...)`
  - `await generate(prompt, ...)` for generic completions.
- Email/price importer ETLs pass a compact preview plus the expected schema; downstream ETL code must
  treat invalid/low-confidence responses as `needs_manual_review`.
