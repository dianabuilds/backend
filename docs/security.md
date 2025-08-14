# Security configuration

## CSRF
- Controlled by environment variables `CSRF_ENABLED`, `CSRF_HEADER_NAME`, `CSRF_COOKIE_NAME`, `CSRF_EXEMPT_PATHS`, `CSRF_REQUIRE_FOR_BEARER`.
- Double submit cookie: value from cookie must match header.
- Applied only to mutating requests when a session cookie (`access_token` or `session`) is present. Paths listed in `CSRF_EXEMPT_PATHS` and `/auth/*` (except `/auth/logout`) are ignored.
- Browser integrations with cookies must send the token from `XSRF-TOKEN` cookie in `X-CSRF-Token` header. Bearer-token calls without cookies do not require CSRF.
- System endpoints like `/health`, `/readyz`, `/metrics` and WebSocket `/ws/notifications` are exempt by default.

## CORS
- Configure allowed origins, headers and methods via `CORS_*` variables.
- In production, `CORS_ALLOWED_ORIGINS` must list explicit domains; `*` is rejected.

## Real IP / trusted proxies
- Enable parsing of client IP from proxy headers with `REAL_IP_ENABLED`.
- `TRUSTED_PROXIES` lists IP addresses or CIDR ranges of proxies.
- `REAL_IP_HEADER` selects which header to read (`X-Forwarded-For`, `Forwarded`, `CF-Connecting-IP`).
- Optional `REAL_IP_DEPTH` selects IP from the chain (1 = last).

## Environment variables
| Variable | Default |
|----------|---------|
| CSRF_ENABLED | true |
| CSRF_HEADER_NAME | X-CSRF-Token |
| CSRF_COOKIE_NAME | XSRF-TOKEN |
| CSRF_EXEMPT_PATHS | /health,/readyz,/metrics,/ws |
| CSRF_REQUIRE_FOR_BEARER | false |
| CORS_ALLOWED_ORIGINS | https://yourdomain.com,https://app.yourdomain.com |
| CORS_ALLOW_CREDENTIALS | True |
| CORS_ALLOWED_METHODS | GET,POST,PUT,DELETE,OPTIONS,PATCH |
| CORS_ALLOWED_HEADERS | Authorization,Content-Type,X-CSRF-Token |
| REAL_IP_ENABLED | false |
| TRUSTED_PROXIES | *(empty)* |
| REAL_IP_HEADER | X-Forwarded-For |
| REAL_IP_DEPTH | *(empty)* |

## Debugging tips
- CSRF failures are logged with reasons in `CSRF reject` messages.
- Rate limiter logs real client IP after processing proxy headers.
- Inspect request headers `Origin`, `X-CSRF-Token` and proxy headers when troubleshooting.
