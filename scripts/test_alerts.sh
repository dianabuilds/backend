#!/usr/bin/env bash
set -euo pipefail

PUSHGATEWAY="${PUSHGATEWAY:-localhost:9091}"

echo "Pushing synthetic metrics to $PUSHGATEWAY"

# High error rate for admin API
curl -sf --data-binary "admin_api_request_total 100\nadmin_api_request_errors_total 10" \
  "http://$PUSHGATEWAY/metrics/job/admin_api_test" >/dev/null

# Spike in no-route transitions
curl -sf --data-binary "transition_no_route_percent 2" \
  "http://$PUSHGATEWAY/metrics/job/no_route_test" >/dev/null

# Spike in quota hits
curl -sf --data-binary "quota_hit_total 200" \
  "http://$PUSHGATEWAY/metrics/job/quota_test" >/dev/null

# High 5xx error rate
curl -sf --data-binary "http_requests_total{status=\"500\",workspace=\"w\",method=\"GET\",path=\"/\"} 10\nhttp_requests_total{status=\"200\",workspace=\"w\",method=\"GET\",path=\"/\"} 10" \
  "http://$PUSHGATEWAY/metrics/job/http_500_test" >/dev/null

# High request latency
curl -sf --data-binary "http_request_duration_ms_sum{workspace=\"w\",method=\"GET\",path=\"/\"} 20000\nhttp_request_duration_ms_count{workspace=\"w\",method=\"GET\",path=\"/\"} 10" \
  "http://$PUSHGATEWAY/metrics/job/slow_request_test" >/dev/null

# 5xx on /nodes/:slug/next
curl -sf --data-binary "http_requests_total{status=\"500\",workspace=\"w\",method=\"GET\",path=\"/nodes/test/next\"} 1" \
  "http://$PUSHGATEWAY/metrics/job/nodes_next_5xx_test" >/dev/null

# High p95 latency on /nodes/:slug/next
curl -sf --data-binary @- "http://$PUSHGATEWAY/metrics/job/nodes_next_latency_test" <<'EOF'
http_request_duration_ms_bucket{le="5",workspace="w",method="GET",path="/nodes/test/next"} 0
http_request_duration_ms_bucket{le="10",workspace="w",method="GET",path="/nodes/test/next"} 0
http_request_duration_ms_bucket{le="25",workspace="w",method="GET",path="/nodes/test/next"} 0
http_request_duration_ms_bucket{le="50",workspace="w",method="GET",path="/nodes/test/next"} 0
http_request_duration_ms_bucket{le="100",workspace="w",method="GET",path="/nodes/test/next"} 0
http_request_duration_ms_bucket{le="250",workspace="w",method="GET",path="/nodes/test/next"} 0
http_request_duration_ms_bucket{le="500",workspace="w",method="GET",path="/nodes/test/next"} 10
http_request_duration_ms_bucket{le="1000",workspace="w",method="GET",path="/nodes/test/next"} 10
http_request_duration_ms_bucket{le="2500",workspace="w",method="GET",path="/nodes/test/next"} 10
http_request_duration_ms_bucket{le="5000",workspace="w",method="GET",path="/nodes/test/next"} 10
http_request_duration_ms_bucket{le="+Inf",workspace="w",method="GET",path="/nodes/test/next"} 10
http_request_duration_ms_count{workspace="w",method="GET",path="/nodes/test/next"} 10
http_request_duration_ms_sum{workspace="w",method="GET",path="/nodes/test/next"} 4000
EOF

echo "Metrics pushed. Check Prometheus for alert status."
