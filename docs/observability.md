# Observability Quickstart

The API and worker services expose Prometheus metrics that describe request traffic and Celery task execution.

## Metrics Endpoints

- API: `http://localhost:8000/metrics` (no auth). Labels: `method`, `route`, `status`.
- Worker: `http://localhost:9097/metrics` by default. Labels: `task`.

The API exports the following metric families:

- `requests_total{method,route,status}` – HTTP request counter.
- `request_duration_seconds{method,route}` – request latency histogram (also exposes `_bucket`, `_count`, `_sum` series).
- `inprogress_requests` – gauge of concurrent in-flight requests.

The worker exports:

- `celery_task_started_total{task}`
- `celery_task_succeeded_total{task}`
- `celery_task_failed_total{task}`
- `celery_task_duration_seconds{task}` histogram.

Set `ENABLE_METRICS=0` or override `METRICS_PORT` to disable or relocate the Celery metrics HTTP server.

## Dashboards

Grafana dashboards are stored under `ops/grafana/dashboards`. Provisioning is configured via `ops/grafana/provisioning/dashboards/dashboards.yaml`, which expects the dashboards to be mounted into `/var/lib/grafana/dashboards/awa`.

To run Grafana/Prometheus locally, mount `ops/grafana/dashboards` into Grafana and `ops/prometheus/prometheus.yml` into Prometheus, then expose the API (`localhost:8000`) and worker (`localhost:9097`) scrape targets.
After the services are running (Grafana defaults to `http://localhost:3000`), configure a Prometheus datasource and import the dashboards.

## k6 Smoke Test

CI runs a non-blocking k6 smoke test (`ops/k6/api_ro/smoke.js`) against the locally started stack. The job uploads `k6-summary.json` as a workflow artifact, visible on the Actions run summary. Failures do not block merges but should be investigated.
