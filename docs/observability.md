# Observability

## Logging

`NavigationService.get_next` writes a trace for each routing decision. The trace lists
all candidates considered, which ones were filtered out, the selected node and an
optional reason. Logs include the trace as structured data under the `trace` field.

## Alert deployment

Prometheus loads alerting rules from `config/prometheus/alerts.yml`. After adding or modifying rules, validate the file and reload Prometheus:

```bash
promtool check rules config/prometheus/alerts.yml
curl -X POST http://localhost:9090/-/reload
```

## Testing alerts

Run `scripts/test_alerts.sh` to push synthetic metrics that trigger the rules and verify alert behavior.

## Tracing

The service can export traces via OTLP. Configure the exporter with the following environment variables:

- `OTEL_EXPORTER_OTLP_ENDPOINT` – OTLP HTTP endpoint, e.g. `http://localhost:4318/v1/traces`.
- `OTEL_EXPORTER_OTLP_HEADERS` – optional headers in `key=value` comma‑separated format.

Example run with tracing enabled:

```bash
APP_ENV_MODE=staging \
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces \
OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer <token>" \
poetry run uvicorn app.backend.app.main:app
```

## Moderation case SLA and notifications

When a moderation case is created the service computes `first_response_due_at` and `due_at` based on `MODERATION_FIRST_RESPONSE_MINUTES` and `MODERATION_RESOLUTION_MINUTES` settings. Notifications are sent to configured emails and an optional Slack webhook so missing responses can be tracked.
