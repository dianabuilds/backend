# Platform IAM

Минимальный IAM: JWT (cookies), CSRF, email verify (mock), SIWE verify (подпись + nonce в Redis).

- API: `api/http.py`
  - `POST /v1/auth/login|refresh|logout|signup|evm/verify` и `GET /v1/auth/verify|evm/nonce`
- Зависимости: `security.py` (`get_current_user`, `csrf_protect`, `require_admin`)
- Адаптеры: `adapters/token_jwt.py`, `adapters/nonce_store_redis.py`, `adapters/verification_store_redis.py`, `adapters/email_via_notifications.py`
- Конфиг: `auth_jwt_*`, `auth_csrf_*`, `admin_api_key`

## TODO
- Подписи SIWE: парсинг всех полей EIP‑4361, строгая проверка домена/uri/chainId/expiration.
- Реальные пользователи/роли: репозиторий пользователей и claims обогащение.
- Refresh‑blacklist/ROTATE/remember‑me: хранение jti/rotation, отзыв токенов.
- Middleware для автоматической CSRF‑проверки на state‑changing методы.
- MFA/2FA и лимиты попыток входа.

