SLO:
- p95 latency < 120ms
- error rate < 0.5%

Метрики:
- platform_<your_domain>_operation_latency_seconds (histogram)
- platform_<your_domain>_errors_total (counter)
- platform_<your_domain>_rate_limit_rejections_total (counter)
- outbox_publish_lag_seconds (если есть события)

