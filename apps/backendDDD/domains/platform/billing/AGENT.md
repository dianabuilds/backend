# AGENT — Billing

Где править:
- Провайдер: `adapters/provider_mock.py` (позже: Stripe/…)
- Репозитории: `adapters/repos_sql.py`
- Сервис: `application/service.py`
- API: `api/http.py` (guard/CSRF на пользовательских/admin ручках)
- Миграции: `schema/sql/001_billing.sql`

Правила:
- Checkout возвращает `provider` и `external_id` (URL может быть `null` для mock).
- Webhook должен проверяться по подписи провайдера (заглушка сейчас всегда `ok`).
- Admin‑guard + CSRF на CRUD планов.

