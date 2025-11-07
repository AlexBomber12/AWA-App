# LLM Microservice

AWA ships a lightweight FastAPI wrapper around a llama.cpp binary so agents can request text completions without depending on third-party APIs. When `LLM_PROVIDER=lan` the application code calls this microservice through the `packages.awa_common.llm.generate` helper.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r services/llm_server/requirements.txt
uvicorn services.llm_server.app:app --host 0.0.0.0 --port 8001
```

The container image used in CI bundles the model at `/models/llama3-q4_K_M.gguf` and the llama.cpp binary at `/llama/main`. On bare metal, mount those paths or override them with environment variables consumed by your process manager.

## Configuration
| Variable | Purpose | Default |
| -------- | ------- | ------- |
| `LLM_PROVIDER` | Selects the backend (`lan`, `openai`, `local`, `stub`). | `lan` |
| `LLM_BASE_URL` | Base URL for the lan microservice when running remote to the API/agents. | `http://localhost:8000` |
| `LLM_API_KEY` | Optional Bearer token sent to the lan service. Leave blank to disable auth. | _empty_ |
| `LLM_TIMEOUT_SECS` | Client-side timeout for lan/local requests. | `60` |
| `LLM_PROVIDER_FALLBACK` | Secondary provider used when the primary errors. | `stub` |

The lan provider uses the OpenAI-compatible `/v1/chat/completions` endpoint exposed by this microservice. The local provider (`LLM_URL`) hits the raw `/llm` route for llama.cpp compatibility testing. Production workloads should use lan so retries and fallbacks are handled centrally.

## API surface
- `GET /health` — returns `{"status": "ok"}` for readiness probes.
- `POST /llm` — accepts `{"prompt": "...", "max_tokens": 256, "temperature": 0.7}` and streams those values into llama.cpp. Successful responses return `{"completion": "..."}`. Errors bubble up as HTTP 500 with a captured stderr snippet.

Wrap the service with your ingress of choice (nginx, Traefik, or docker-compose sidecar) and enforce TLS when exposing it outside the cluster.

## Integration with AWA-App
- Agents/services set `LLM_PROVIDER=lan` plus `LLM_BASE_URL=http://llm:8001` (or the in-cluster DNS name).
- Requests originate from the worker and API containers via `httpx.AsyncClient`. Configure `LLM_TIMEOUT_SECS` between 30–60 seconds; retries are managed by the calling code, so surfacing errors quickly keeps queues flowing.
- If `LLM_API_KEY` is set, the helper automatically adds `Authorization: Bearer <token>` headers so the microservice can enforce shared secrets or mTLS.
- When the lan service is unavailable the helper rotates through `LLM_PROVIDER_FALLBACK` (default `stub`) to keep upstream pipelines alive while emitting warnings.

## Observability
- Uvicorn logs every `/llm` request with latency information; ship them to the same Loki target as other services.
- Add the `/health` endpoint to the compose `healthcheck` so Kubernetes or docker-compose restarts the container if llama.cpp crashes.

## See also
- [LLM provider options](LLM.md)
- [Agents](agents.md)
- [Testing](TESTING.md)
