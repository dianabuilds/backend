# Platform Billing

Планы/подписки/платежи (MVP, внутренний провайдер).

- Доменные модели: `domain/models.py` (`Plan`, `Subscription`, `LedgerTx`)
- Порты: `ports.py` (`PaymentProvider`, `PlanRepo`, `SubscriptionRepo`, `LedgerRepo`)
- Адаптеры: `adapters/provider_mock.py`, `adapters/repos_sql.py`
- Сервис: `application/service.py`
- API: `api/http.py`
  - Публично: `GET /v1/billing/plans`
  - Пользователь: `POST /v1/billing/checkout`
  - Вебхук: `POST /v1/billing/webhook`
  - Admin: `POST/DELETE /v1/billing/admin/plans*`
- Миграции: `schema/sql/001_billing.sql`

## TODO
- Реальный провайдер (Stripe/…): подпись вебхуков, идемпотентность, статусы.
- Интеграция с Quota по планам, события `plan.changed.v1`.
- Статус подписки: `GET /v1/billing/subscriptions/me`.
- Аудит действий admin, метрики биллинга.

