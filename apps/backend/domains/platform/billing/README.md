# Платёжный биллинг (EVM)

Документ описывает текущую реализацию домена `domains.platform.billing`: архитектуру, ключевые сущности, потоки данных и интеграции. Модуль обеспечивает on-chain биллинг в EVM-сетях, управление планами и обзор для команды finance/ops.

## Архитектура

```
domains/platform/billing
├─ api
│  ├─ public/                # checkout, history, me/*
│  ├─ admin/                 # CRUD для планов/контрактов/провайдеров
│  └─ overview/              # dashboards для finance_ops
├─ application
│  ├─ service.py             # BillingService: checkout, ledger, webhooks
│  └─ use_cases/             # слой сценариев (public/admin/overview/settings)
├─ adapters
│  ├─ provider_evm.py        # on-chain провайдер (checkout + verify_webhook)
│  ├─ repos_sql.py           # SQL-адаптеры планов, подписок, ledger
│  └─ workers/               # фоновые воркеры по событиям контрактов
├─ metrics.py                # Prometheus-метрики (транзакции, планы, сети)
├─ schema/sql/               # миграции 001_billing.sql, 002_contracts.sql, …
└─ tests/                    # unit и integration тесты домена
```

DI-конфигурация находится в `apps/backend/domains/platform/billing/wires.py`. Новые зависимости (crypto_config, провайдеры, метрики, события) регистрируются в контейнере платформы.

## Сущности

- **SubscriptionPlan** — описание тарифа (цены, интервалы, токены, привязка к контракту и gateway).
- **PaymentContract** — on-chain смарт-контракт, привязанный к плану (chain_id, ABI, методы mint/burn, RPC fallback).
- **PaymentGateway** — адаптер провайдера; для EVM хранит сетевые параметры, подписи, настройки retries.
- **PaymentTransaction** — запись в ledger с информацией о сетях, токене, tx hash, статусах и связанной сущности (product_type/product_id).
- **Subscription** — активная или отложенная подписка пользователя; включает задолженность и дату следующего списания.

## Основные потоки

### Checkout
1. `POST /v1/billing/checkout` (публичный use-case) принимает план, user_id и wallet.
2. `BillingService.checkout` создаёт запись в ledger со статусом `pending`, фиксирует идемпотентность и вызывает `provider_evm.checkout`.
3. Провайдер формирует payload кошелька (to, value, data, gas, deadline) на основании настроек контракта и подписывает challenge.
4. Клиент получает payload и отправляет транзакцию в сеть. При повторном вызове выдаётся тот же ledger_id.

### Webhook / события контрактов
1. Контракт/relay вызывает `POST /v1/billing/contracts/webhook` → `PublicBillingUseCases.handle_contracts_webhook`.
2. `BillingService.handle_webhook` проверяет подпись, применяет идемпотентный слой по external_id/tx_hash, обновляет ledger и подписки, публикует события (`billing.plan.changed.v1`), вызывает уведомления и аудит.
3. Фоновый воркер `workers/contracts_listener.py` подписывается на on-chain события и ретраит в случае задержки подтверждений.

### Overview & профиль
- `GET /v1/billing/overview/*` суммирует метрики по сетям, токенам, доходу (использует `SQLBillingAnalyticsRepo` и `metrics.py`).
- `BillingSettingsUseCase.build_bundle` объединяет данные профиля: подтверждённый wallet, задолженность, статус последнего платежа, историю (`/v1/billing/me/history`).

## Интеграции

- **Quota** — публикуется событие `billing.plan.changed.v1` при успешном платеже (обновляет лимиты продуктов).
- **Notifications** — триггеры для пользователя и ops (успешная оплата, просрочка, сбой).
- **Audit** — запись всех действий admin (изменения планов, контрактов, ручные операции) и платёжных событий.
- **Finance Ops** — отдельная роль доступа; ручки overview требуют `require_finance_ops`.

## Данные и миграции

Миграции `schema/sql/00*_*.sql` поддерживают:
- расщепление `product_type/product_id` для связей с продуктами;
- хранение `token`, `network`, `tx_hash`, `confirmed_at`, `failure_reason` в `payment_transactions`;
- поля `gateway_slug`, `contract_slug`, `interval`, `price_token`, `price_usd_estimate` у планов;
- расширенные параметры контрактов (`chain_id`, `abi`, `mint_method`, `burn_method`, `webhook_secret`, `fallback_rpc`);
- нормализованную таблицу `crypto_config` (RPC, retries, gas cap, fallback сети).

## Метрики и наблюдаемость

- Prometheus-гейджи и счётчики в `metrics.py`: активные подписки, MRR/ARPU, статус транзакций, объём по сетям/токенам, события контрактов.
- OpenTelemetry-интеграция (`infra/observability/opentelemetry.py`) экспонирует `/v1/metrics`. При отсутствии зависимостей ручка возвращает `503`.
- Структурированные логи включают `tx_hash`, `user_id`, `contract_slug`. Алёрты описаны в `docs/playbooks/performance.md`.

## Тестирование

- Юнит-тесты: `tests/unit/billing/*` покрывают сервис checkout/webhook, use-cases, провайдер, воркер.
- Интеграционные тесты: `tests/integration/billing/*` проверяют API, idempotency и overview.
- Smoke-тесты используют тестовую БД (`APP_DATABASE_URL`), моки IAM и RPC.

## Развёртывание и конфигурация

- Требуются переменные: `BILLING_RPC_CONFIG`, `BILLING_EVM_GATEWAYS`, `BILLING_WEBHOOK_SECRET`, `APP_BILLING_FINANCE_OPS_USER_ID` и др. описаны в `.env.example`.
- Перед релизом: прогнать миграции, убедиться в доступности RPC endpoint и ключей подписи, обновить Quota/notifications/audit конфигурацию, включить воркеры.

## Дополнительные ресурсы

- `docs/features/billing/blueprint.md` — расширенный blueprint решения.
- `docs/features/billing/tasks.md` — чек-лист задач и статусы.
- `docs/playbooks/billing.md` — playbook и сценарии реагирования (см. обновления в этой задаче).
- `apps/backend/scripts/billing_e2e.py` — сценарий полного цикла checkout → webhook → событий.
