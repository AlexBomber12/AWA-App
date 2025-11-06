# Observability Baseline

## SLO and SLI Targets
- API availability: 99.9% measured over 30 days
- API latency: p95 ≤ 400 ms and p99 ≤ 800 ms measured on 1 minute windows
- API error rates: 5xx ≤ 0.5%; 4xx (excluding 401/403) ≤ 1.0%
- Celery task success ratio ≥ 99% on rolling 24 h
- Celery queue wait time p95 ≤ 30 s
- ETL currency: daily pipelines complete by T+1 07:00 local; hourly feeds lag ≤ 15 minutes

## Standard Metric Labels
- Global: `service`, `env`, `version`
- HTTP: `method`, `path_template`, `status`
- Celery tasks: `task_name`, `outcome`, `exc_type`
- ETL pipelines: `pipeline`
- Queue backlog: `queue`

## PromQL Snippets
```promql
# Availability
1 - (sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])))

# Latency (p95 / p99)
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# Error rates
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
sum(rate(http_requests_total{status=~"4..",status!="401",status!="403"}[5m])) / sum(rate(http_requests_total[5m]))

# Celery success ratio
sum(rate(task_runs_total{outcome="success"}[5m])) / sum(rate(task_runs_total[5m]))

# Queue backlog
max(queue_backlog) by (queue, service, env)

# ETL latency p95
histogram_quantile(0.95, sum(rate(etl_latency_seconds_bucket[5m])) by (le, pipeline))
```

## Alerting Rules (Prometheus Examples)
```yaml
groups:
  - name: awa-observability
    rules:
      - alert: api_high_latency_p95
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 0.4
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "API latency p95 above SLO threshold"
      - alert: api_high_latency_p95_crit
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 0.8
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "API latency p95 breaching critical threshold"
      - alert: api_error_rate_5xx
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.005
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "API 5xx error rate elevated"
      - alert: etl_high_latency
        expr: histogram_quantile(0.95, sum(rate(etl_latency_seconds_bucket[5m])) by (le, pipeline)) > 900
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "ETL latency p95 above threshold"
      - alert: celery_low_success_ratio
        expr: 1 - (sum(rate(task_runs_total{outcome="success"}[5m])) / sum(rate(task_runs_total[5m]))) > 0.01
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Celery task success ratio below 99%"
      - alert: queue_backlog_high
        expr: max(queue_backlog) by (queue, service, env) > 100
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Queue backlog elevated"
```

## Deployment Notes
- FastAPI deployments behind Gunicorn/Uvicorn should set `PROMETHEUS_MULTIPROC_DIR` to a writable, empty directory and ensure it is cleaned on startup so `/metrics` aggregates all workers correctly.
- Celery workers can expose metrics by setting `WORKER_METRICS_HTTP=1` and `WORKER_METRICS_PORT=9108`. A background thread samples queue backlog when Redis is configured as the broker.
- For backlog gauges, export `QUEUE_NAMES` with a comma-separated list of Celery queues. Non-Redis brokers skip backlog sampling safely.
- Keep metric label cardinality low by using `path_template` instead of raw request paths and avoiding unbounded identifiers.
