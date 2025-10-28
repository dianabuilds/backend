SLO:
- p95 update_username < 120ms
- p95 email_request < 200ms
- p95 email_confirm < 200ms
- p95 wallet_bind < 200ms
- p95 wallet_unbind < 200ms

Метрики:
- domain_profile_update_username_latency_seconds (histogram)
- outbox_publish_lag_seconds
- profile_settings_operation_latency_seconds{operation="email_request|email_confirm|wallet_bind|wallet_unbind"}
