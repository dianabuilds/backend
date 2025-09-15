# AGENT — IAM

Где править:
- `security.py` — зависимости `get_current_user`, `csrf_protect`, `require_admin`.
- `api/http.py` — ручки логина/рефреша/выхода/SIWE.
- `adapters/*` — JWT/nonce/email/verification.

Правила:
- JWT только в cookies (HttpOnly) + CSRF cookie/заголовок для методов с телом.
- SIWE: проверка подписи и nonce из Redis, добавить строгую валидацию полей при усилении безопасности.
- Admin‑guard: либо `X-Admin-Key`, либо `role=admin` в claims.

