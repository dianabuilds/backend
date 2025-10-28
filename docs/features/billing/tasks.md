# Задачи по биллингу и EVM-интеграции

## 1. Схема данных и миграции
- [x] Исправить `payment_transactions`: заменить дублирующее поле `id` на `product_type`/`product_id`, добавить `token`, `network`, `tx_hash`, `confirmed_at`, `failure_reason` (`apps/backend/domains/platform/billing/schema/sql/001_billing.sql`).
- [x] Добавить в `subscription_plans` ссылки на `gateway_slug`, `contract_slug`, `interval`, `price_token`, `price_usd_estimate`.
- [x] Расширить `payment_contracts` полями `chain_id`, `abi`, `mint_method`, `burn_method`, `webhook_secret`, `fallback_rpc` (`schema/sql/002_contracts.sql`).
- [x] Привести `crypto_config` к нормализованному виду: хранить структуры RPC endpoint, retries, gas_cap, fallback сетей (`schema/sql/003_crypto_config.sql`).

## 2. Провайдер и checkout
- [x] Реализовать `provider_evm` (новый адаптер) с методами `checkout`/`verify_webhook`, генерацией payload для wallet и валидацией подписи (`apps/backend/domains/platform/billing/adapters`).
- [x] Обновить `BillingService.checkout` для записи в ledger статуса `pending` и возврата детализированного payload (`application/service.py`).
- [x] Доработать `PublicBillingUseCases.checkout` для логирования идемпотентности и расширенного ответа (`application/use_cases/public.py`).
- [x] Настроить DI в `wires.py` для использования нового провайдера, конфигурации RPC из `crypto_config`.

## 3. Webhook и обработка событий
- [x] Реализовать idempotency layer в `service.handle_webhook` с проверкой `external_id`/`tx_hash` и повторной защитой от дублей (`application/service.py`).
- [x] Расширить `PublicBillingUseCases.handle_contracts_webhook`: хранить исходные payload, обрабатывать статусы `failed`, `refunded`, валидировать ABI методы (`application/use_cases/public.py`).
- [x] Создать фонового воркера (`domains/platform/billing/workers`) для подписки на on-chain события, ретраев и синхронизации ledger.
- [x] Добавить юнит- и интеграционные тесты на webhook/idempotency/worker (`tests/unit/billing`, `tests/integration`).

## 4. Admin/Overview API
- [x] Расширить use-case `PlansAdminUseCase` для редактирования связок план↔контракт↔gateway и отображения токена/интервала (`application/use_cases/plans_admin.py`).
- [x] Обновить admin ручки для планов, провайдеров, контрактов с новыми полями и валидацией (`api/admin/*.py`).
- [x] Создать новый модуль `api/overview` + `application/use_cases/overview.py` с маршрутами `/v1/billing/overview/*` (dashboard, networks, payouts).
- [x] Перенести операторские метрики с `/admin/*` в overview и выделить роль `support` (`docs/reference/api/access-policy.md` + проверки `require_role_db("support")`).

## 5. Профиль и пользовательский опыт
- [x] Обновить `BillingSettingsUseCase.build_bundle`: подтягивать подтверждённый wallet, задолженность, статусы последнего платежа (`application/use_cases/settings.py`).
- [x] Расширить API `/v1/billing/me/history` выводом tx hash, сети, token, gas (`api/public/subscriptions.py`).
- [x] Синхронизировать с profile-service схему хранения wallet и SIWE-логики (`domains/product/profile`).

## 6. Метрики и наблюдаемость
- [x] Добавить Prometheus-метрики для транзакций, подписок, сетей и контрактов (`application/service.py`, `adapters/sql/analytics.py`).
- [x] Обновить `SQLBillingAnalyticsRepo` для расчёта `MRR`, `ARPU`, разрезов по токенам и сетям (`infrastructure/sql/analytics.py`).
- [x] Настроить алерты (docs/playbooks/performance.md) на отклонения: рост ошибок, задержки подтверждения, деградацию RPC.
- [x] Включить структурированные логи с `tx_hash`, `user_id`, `contract_slug` (`application` и `workers`).

## 7. Интеграции
- [x] Отправлять событие `plan.changed.v1` в Quota после успешного платежа (`application/service.py` → `packages/events`).
- [x] Добавить уведомления пользователю/ops об оплате, просрочках, сбоях (`domains/platform/notifications`).
- [x] Подключить аудит всех admin операций и платежных событий (`domains/platform/audit`).

## 8. Финальные шаги
- [x] Обновить документацию и README домена (`apps/backend/domains/platform/billing/README.md`).
- [x] Добавить раздел “Billing Overview” в `docs/reference/api/catalog.md`.
- [x] Провести end-to-end тест (script) для полного жизненного цикла подписки (checkout → on-chain tx → webhook → quota update).
- [x] Подготовить rollout-план и playbook реагирования на инциденты (docs/playbooks/billing.md).

## 9. UI и операторский контур (в разработке)

### 9.1 Синхронизация API ↔ фронтенд
- [x] Обновить `fetchBillingKpi` и `fetchBillingMetrics` так, чтобы они разворачивали вложенные структуры `kpi/subscriptions` и возвращали корректные числа.
  - [x] Расширить типы `BillingMetrics`, `BillingKpi` дополнительными полями (дельты, временные ряды), либо добавить отдельный тип `BillingOverviewResponse`.
  - [x] Привести `useManagementPayments` и `useManagementTariffs` к новой схеме, обеспечить обработку `loading/error`.
- [x] Расширить `BillingPlan`/`BillingPlanPayload` полями `_PLAN_FIELDS` (token, interval, gateway_slug, contract_slug, price_usd_estimate).
  - [x] Обновить сериализацию в `TariffsView` для сохранения нетронутых значений.
  - [x] Добавить тесты типов и снапшоты API-моков.
- [x] Переписать `saveBillingProvider`/`deleteBillingProvider` вызовы: передавать `networks`, `supported_tokens`, `default_network` отдельными полями, формировать `config` на бекенде.
  - [x] Реализовать адаптер преобразования формы → payload + обратный маппинг payload → форму.

### 9.2 Страница Overview
- [x] Реализовать карточки KPI с вычислением дельт, отображением знаков и ссылками на фильтры.
- [x] Добавить компонент графика выручки с вкладками Net/Gross (`recharts` или `apexchart`) и экспортом.
- [x] Сформировать секцию сегментов планов: данные берём из `subscriptions.tokens/networks`, группируем на фронте.
- [x] Собрать таблицу сетей и правую колонку (кошелёк, выплаты, задолженность).
- [x] Внедрить ленту инцидентов: подключить `fetchBillingOverviewPayouts` и логи Observability (при наличии API).

### 9.3 Payments Workspace
- [x] Ввести вкладочный layout (Providers, Contracts, Transactions, Crypto) с сохранением состояния.
- [x] Провайдеры:
  - [x] Таблица с колонками `slug`, `type`, `enabled`, `networks`, `tokens`, `priority`, `contract`.
  - [x] Детальная карточка/Drawer с секциями и JSON-просмотром.
  - [x] Форма создания/редактирования с валидацией и предварительным просмотром payload.
- [x] Контракты:
  - [x] Карточки и таблица ключевых параметров.
  - [x] Таймлайн событий (ленивая загрузка, пагинация) + ссылки на блокчейн-эксплореры.
- [x] Транзакции:
  - [x] Панель фильтров (статус/провайдер/контракт/сеть/диапазон дат/сумма).
  - [x] Таблица с закреплением колонок и меню действий.
  - [x] Drawer детализации с историей статусов и расчётом комиссий.
- [x] Крипто-настройки:
  - [x] Форма редактирования списков RPC, fallback сетей, gas cap, retries.
  - [x] Кнопка «Проверить соединение» (вызывает бэкенд-тест/ моковый endpoint).
  - [x] Журнал изменений (история сохранений с датой/автором).

### 9.4 Tariffs (планы)
- [x] Секции KPI по планам и эксперименты.
- [x] Каталог карточек планов с фильтрами.
- [x] Полноэкранный редактор с вкладками «Общие», «Лимиты», «Особенности», «История», «Предпросмотр».
  - [x] Сохранение/валидация полей, отображение ошибок бэкенда.
  - [x] Интеграция с `/audit` для таймлайна и диффа.
- [x] Режим матричного редактирования лимитов с трекингом изменённых ячеек.

### 9.5 Тестирование и контроль качества
- [x] Написать unit-тесты для обновлённых хуков (`useManagementPayments`, `useManagementTariffs`, новый `useBillingOverview`).
- [x] Добавить компонентные тесты (React Testing Library) для KPI, таблиц, drawer.
- [x] Подготовить Storybook story для каждой ключевой секции (Overview, Providers, Plan Card).
- [x] Настроить e2e сценарии (Cypress) для главных пользовательских путей (просмотр KPI, редактирование провайдера, изменение плана).




