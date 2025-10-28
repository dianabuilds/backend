# Blueprint биллинга с поддержкой EVM

Документ фиксирует целевую архитектуру и функциональные требования биллинга после внедрения on-chain провайдера и operator overview. Используется для синхронизации команд платформы, продукта и инфраструктуры.

## 1. Цели

- Поддержка подписок и разовых платежей в EVM-сетях (Ethereum mainnet/testnet + совместимые L2).
- Разделение пользовательских сценариев (checkout, профиль) и операторского обзора support.
- Единая система учёта (ledger) с on-chain подтверждениями, уведомлениями и аудитом.
- Полноценная наблюдаемость: метрики, структурированные логи, алерты, дашборды.

## 2. Компоненты

| Слой | Назначение | Основные файлы |
| --- | --- | --- |
| API (public/admin/overview) | REST-ручки для клиентов, админов, support | `domains/platform/billing/api/*` |
| Application Service | Единый сервис оплаты: checkout, ledger, webhook | `application/service.py` |
| Use Cases | Оркестрация для контуров (public, settings, admin, overview) | `application/use_cases/*` |
| Адаптеры | Провайдер EVM, SQL репозитории, воркеры, интеграции | `adapters/*`, `workers/*` |
| Схема данных | Миграции, контракты БД, crypto_config | `schema/sql/*.sql` |
| Инфраструктура | Аналитика, события, observability | `infrastructure/sql/`, `metrics.py`, `packages/events` |

Диаграмму взаимосвязей см. в `README.md` (раздел «Архитектура»).

## 3. Потоки

### Checkout
1. Пользователь выбирает план → `/v1/billing/checkout`.
2. Use-case выполняет проверки (активная подписка, задолженность, wallet), передаёт контекст в `BillingService.checkout`.
3. Сервис создаёт ledger-транзакцию (`pending`), регистрирует идемпотентный ключ, вызывает `provider_evm.checkout`.
4. Провайдер собирает payload: `to`, `value`, `data`, `gas`, `chain_id`, `deadline`, `nonce`, подпись HMAC.
5. Ответ API содержит: `ledger_id`, `transaction_payload`, `network`, `token`, `instructions`.

### On-chain подтверждение
1. Контракт вызывает webhook напрямую или через relay → `/v1/billing/contracts/webhook`.
2. `BillingService.handle_webhook`:
   - проверяет подпись/секрет;
   - выполняет идемпотентную проверку по `external_id` + `tx_hash`;
   - обновляет ledger (`succeeded/failed/refunded`) и подписку;
   - публикует `billing.plan.changed.v1` (Quota), создаёт уведомления, записывает события аудита.
3. Фоновый воркер подписывается на события контрактов и дополняет webhook при задержках.

### Overview для support
1. `/v1/billing/overview/dashboard` — агрегированные метрики: MRR, ARPU, активные подписки, задолженность.
2. `/v1/billing/overview/networks` — разрез по сетям/токенам, провалившимся/ожидающим транзакциям.
3. `/v1/billing/overview/payouts` — статусы контрактов, остаток, прогнозы кэшфлоу.
Доступ ограничен ролью `support`, логику проверяет `require_role_db("support")`.
В UI операторский контур доступен по маршрутам `/finance/billing/*`, в отличие от пользовательской страницы `/billing`.

### Пользовательский профиль
- `BillingSettingsUseCase.build_bundle` подтягивает подтверждённый wallet, задолженность, статусы последних транзакций, активные планы.
- `/v1/billing/me/history` возвращает детализацию (tx hash, сеть, token, gas, value_usd).
- Интеграция с profile-service синхронизирует SIWE и хранение wallet.

## 4. UI операторского контура

Раздел `/finance/billing/*` состоит из трёх ключевых страниц. Ниже приведены текстовые макеты с привязкой к данным.

### 4.1 Overview (операторская приборная панель)
- Верхняя полоса KPI: карточки «Активные подписки», «MRR», «ARPU», «Churn 30d», «Просроченные счета». Каждая карточка отображает текущее значение, дельту к предыдущему периоду, цветовую индикацию и ссылку-быстрый фильтр.
- Блок «Выручка»: компактный area-chart за выбранный период (7/30/90 дней), вкладки «Net»/«Gross», кнопка экспорта CSV, подписи с последними аномалиями.
- Сегменты подписок: плитки по каждому плану (Plan slug, активных/пробных/отвалившихся), по клику открывается боковая панель с когортами.
- Сводка сетей: таблица (сеть, токен, успешность, объём, среднее подтверждение), разворот строки показывает мини-график и топ-3 контракта.
- Лента инцидентов: хронологический список событий (`overview.payouts`, алерты Observability), содержит ссылку на плейбук/тикет.
- Правая колонка: статус подтверждения кошелька, расписание ближайших выплат, краткая детализация задолженности (ссылки на профиль пользователя).

### 4.2 Payments Workspace
- Общие вкладки: «Провайдеры», «Контракты», «Транзакции», «Крипто-настройки». Вкладки сохраняют URL (query `?tab=`) и состояние фильтров.
- Глобальная шапка вкладки отображает индикаторы загрузки и ошибки, приходящие из `useManagementPayments`.
- Провайдеры: двухколоночный макет (слева таблица, справа карточка детали).
  - Таблица: колонки `slug`, `type`, `enabled`, `networks`, `supported tokens`, `priority`, `contracts`. Фильтры по сети и статусу.
  - Деталь: секции «Маршрутизация» (priority, fallback), «Поддержка» (networks, токены, default network), «Связи» (contract_slug, SLA), JSON-просмотр (read-only).
  - Drawer создания/редактирования с типизированными полями, подсказками и превью итогового payload.
- Контракты: карточки с ключевыми параметрами (chain, testnet, enabled, последние события), таймлайн событий под карточкой, лента последних вебхуков, кнопка «Проверить ABI».
- Транзакции: расширенный фильтр (статус, провайдер, контракт, дата, сумма, сеть). Таблица поддерживает закрепление колонок, в строках — выпадающее меню действий (пометить, создать инцидент, открыть в блокчейн-эксплорере). Детальный drawer показывает историю статусов, связанные ledger-записи и расчёт комиссий.
- Крипто-настройки: форма с редакторами списков (RPC endpoints, fallback сети), числовыми полями (retries, gas cap), кнопкой «Проверить соединение» и журналом изменений.

### 4.3 Tariffs (планы)
- Заголовок с карточками «Всего планов», «Активных», «MRR по топ-3 планам», «Эксперименты».
- Каталог планов: карточки с названием, ценой, интервалом (переключатель month/year), основными лимитами (badge), тегами аудитории, индикатором статуса. Над карточками — поиск и фильтры (статус, токен, аудитория).
- При выборе плана открывается полноэкранный редактор с вкладками:
  - «Общие» — поля slug (только чтение для существующих), название, описание, цена, валюта, токен, интервал, связанный контракт/провайдер, флаги публикации.
  - «Лимиты» — таблица editable со всеми ключами, подсказками и вычислением «Итого»; подсветка изменённых значений.
  - «Особенности» — булевые переключатели, списки аудиторий, модели, A/B конфигурация.
  - «История» — таймлайн версий с дифф-просмотром и кнопкой отката.
  - «Предпросмотр» — отображение карточки так, как она выглядит на публичном сайте.
- Режим «Матричное редактирование лимитов» открывает отдельный экран-таблицу (планы × лимиты) с массовым изменением, состоянием «черновик» до сохранения.

## 5. Логика синхронизации фронтенда и API

- `/v1/billing/overview/dashboard` → фронтенд преобразует `kpi` и `subscriptions` в массив KPI карточек и данные для графиков. Дельты вычисляются на клиенте (разница между последними точками timeseries либо дополнительным полем `kpi_prev`, если появится).
- `/v1/billing/admin/providers` и `saveBillingProvider`: UI отправляет явно поля `slug`, `type`, `enabled`, `priority`, `contract_slug`, а конфигурации (`networks`, `supported_tokens`, `default_network`) собираются в структурированном объекте; JSON-просмотр формируется после успешной валидации формы.
- `/v1/billing/admin/contracts` + `/events`: ленту событий подгружаем лениво при открытии детализации (AbortController для отмены). UI хранит `contractsById` для связывания событий и провайдера.
- `/v1/billing/admin/transactions`: фильтры формируют query-параметры (`status`, `provider`, `contract`, `from`, `to`, `min_amount`, `max_amount`, `network`). При добавлении пагинации сервером предпочтительно перейти на `cursor` (UI хранит стек курсоров).
- `/v1/billing/overview/crypto-config`: после обновления UI вызывает повторный `fetch` и отображает diff/лог активности.
- `/v1/billing/admin/plans/all` + `saveBillingPlan`: фронтенд сериализует payload, сохраняя нетронутые поля (`billing_interval`, `price_token`, `gateway_slug`, `contract_slug`). В истории используется `/audit`, а для матрицы лимитов `bulk_limits`.

## 6. Данные

- **payment_transactions** — хранит `product_type/product_id`, `network`, `token`, `tx_hash`, `gas_used`, `confirmed_at`, `failure_reason`.
- **subscription_plans** — включает `gateway_slug`, `contract_slug`, `interval`, `price_token`, `price_usd_estimate`.
- **payment_contracts** — `chain_id`, `abi`, `mint_method`, `burn_method`, `webhook_secret`, `fallback_rpc`, `limits`.
- **crypto_config** — описывает RPC endpoints, retries, gas cap и fallback сети.

Миграции поддерживают reversible-up/down; для тестов используется `pytest fixture` с прогоном всех файлов в порядке.

## 7. Интеграции

- **Quota** — событие `billing.plan.changed.v1` (user_id, план, предыдущий статус, новый статус, ledger_id).
- **Notifications** — шаблоны для пользователя и ops: успешная оплата, просрочка, отказ, manual intervention.
- **Audit** — протоколирует действия admin (создание/редактирование планов, контрактов, gateway), а также каждое изменение статуса транзакции.
- **Scheduler/Worker** — `contracts_reconciliation_worker` обеспечивает повторные проверки транзакций, если webhook не пришёл.

## 8. Наблюдаемость и SLO

- Prometheus-метрики (`metrics.py`): `billing_transactions_total`, `billing_subscriptions_active`, MRR/ARPU, распределение по сетям.
- `/v1/metrics` объединяет OpenTelemetry данные и custom регистры.
- Структурированные логи включают `tx_hash`, `user_id`, `contract_slug`. Трейсы — через OTLP → Grafana Tempo.
- SLO: успешность подтверждений ≥ 98% за 10 минут, error rate checkout < 1%, задержка webhook < 2 minutes.
- Плейбуки: `docs/playbooks/performance.md`, `docs/playbooks/billing.md`.

## 9. Безопасность

- Webhook подписан `webhook_secret` (HMAC-SHA256 + timestamp window).
- Настройки провайдера и RPC конфигурации хранятся в Vault/Secret Manager, в рантайме попадают через `BILLING_EVM_GATEWAYS/CRYPTO_CONFIG`.
- Роль `support` отделена от `admin`: только чтение агрегатов, без права модификации планов.
- Аудит событий доступен security/ops через `/v1/admin/audit`.

## 10. Тестирование

- Юнит: провайдер, сервисы, use-case admin/overview (`tests/unit/billing/*`).
- Интеграция: checkout → webhook → ledger (`tests/integration/billing/test_checkout_flow.py`), overview API.
- Smoke: `tests/smoke/test_api_billing.py` — использует тестовые DSN, моки IAM.
- Контрактные тесты событий Quota (`tests/contracts/events/test_billing_plan_changed.py`).

## 11. Rollout (сводно)

1. Прогнать миграции `Schema v3`.
2. Задать переменные окружения (RPC, приватные ключи, секреты).
3. Обновить Quota и notifications схемы.
4. Проверить дашборды Prometheus/Grafana, SLO алерты.
5. Включить воркеры и убедиться, что `/v1/billing/overview/*` отдаёт данные.

Полная инструкция — в `docs/playbooks/billing.md` (раздел «Rollout»).

## 12. Roadmap (follow-up)

1. Мультивалютные планы (USDC/DAI), автоматическая конвертация в USD.
2. Fallback custodial-кошельки для enterprise.
3. Расширенные отчёты support (планы → выручка → churn).
4. Self-service управление лимитами пользователем.
5. Поддержка fiat-провайдеров через unified gateway API.


