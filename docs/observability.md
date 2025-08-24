# Observability

## Alert deployment

Prometheus loads alerting rules from `config/prometheus/alerts.yml`. After adding or modifying rules, validate the file and reload Prometheus:

```bash
promtool check rules config/prometheus/alerts.yml
curl -X POST http://localhost:9090/-/reload
```

## Testing alerts

Run `scripts/test_alerts.sh` to push synthetic metrics that trigger the rules and verify alert behavior.
