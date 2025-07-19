# LLM provider options

The application can talk to a language model via different providers.

* `LLM_PROVIDER=lan` (default) points to a FastAPI service exposing the OpenAI
  chat completions API. Configure `LLM_BASE_URL` and optional `LLM_API_KEY` to
  reach the microservice.
* `LLM_PROVIDER=openai` uses the official API. Supply `OPENAI_API_KEY` and
  optionally `OPENAI_MODEL`.
* `LLM_PROVIDER=local` runs against a locally hosted Llama.cpp server specified
  by `LLM_URL`.
