# Environment variables

Key variables used by the service. See `.env.example` for full list.

| Variable | Purpose | Default/Example |
|----------|---------|-----------------|
| `DATABASE__HOST` | PostgreSQL host | `postgres` |
| `DATABASE__PORT` | PostgreSQL port | `5432` |
| `DATABASE__NAME` | Database name | `app` |
| `DATABASE__USERNAME` | DB user | `app` |
| `DATABASE__PASSWORD` | DB password | `change_me` |
| `JWT__SECRET` | JWT signing secret | `change_me_auth_jwt_secret` |
| `JWT__ALGORITHM` | JWT algorithm | `HS256` |
| `JWT__EXPIRES_MIN` | Access token lifetime (minutes) | `1440` |
| `COOKIE_DOMAIN` | Domain for auth cookies | `yourdomain.com` |
| `PAYMENT__JWT_SECRET` | Payment JWT secret | `change_me_payment_secret` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated origins | `https://yourdomain.com` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `SMTP_MOCK` | Disable real email sending when `True` | `True` |
| `SMTP_HOST` | SMTP host | `smtp.example.com` |
| `SMTP_PORT` | SMTP port | `587` |

Keep secrets like JWT and SMTP credentials outside VCS; store them in local `.env`.
