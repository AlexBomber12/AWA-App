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
