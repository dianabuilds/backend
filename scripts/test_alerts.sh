#!/usr/bin/env bash
set -euo pipefail

PUSHGATEWAY="${PUSHGATEWAY:-localhost:9091}"

echo "Pushing synthetic metrics to $PUSHGATEWAY"

# High error rate for admin API
curl -sf --data-binary "admin_api_request_total 100\nadmin_api_request_errors_total 10" \
  "http://$PUSHGATEWAY/metrics/job/admin_api_test" >/dev/null

# Spike in no-route transitions
curl -sf --data-binary "transition_no_route_percent 50" \
  "http://$PUSHGATEWAY/metrics/job/no_route_test" >/dev/null

# Spike in quota hits
curl -sf --data-binary "quota_hit_total 200" \
  "http://$PUSHGATEWAY/metrics/job/quota_test" >/dev/null

echo "Metrics pushed. Check Prometheus for alert status."
