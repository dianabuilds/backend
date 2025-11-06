# Backend-библиотека для биллинга

Документ описывает требования к серверной библиотеке, которая интегрирует приложения с EVM-контрактами (`PlanManager`, `SubscriptionManager`, `Marketplace`) из каталога `apps/crypto/evm`. Библиотека служит связующим звеном между on-chain логикой и внутренними сервисами.

## Цели
- Предоставить высокоуровневый API для работы с планами, подписками и маркетплейсом.
- Обеспечить корректную генерацию EIP-712 подписей и управление солями.
- Сформировать точку интеграции с платёжным шлюзом и системой ролей.
- Упростить тестирование и симуляцию сценариев с использованием Hardhat/Anvil.

## Основные модули

### 1. Управление ролями (`roles`)
- `grantRole(role, account)` / `revokeRole(role, account)` — обёртки над `CoreSystem`.
- `ensureRoles(config)` — инициализация ролей согласно конфигурации окружения (например, один кошелёк в dev, несколько в prod).
- Хелперы для проверки прав: `isAuthor(account)`, `isOperator(account)`, `isAutomation(account)`.
- Логи с фиксацией tx hash, чтобы отслеживать изменения доступа.

### 2. Планов и подписей (`plans`)
- Генерация структуры `SignatureLib.Plan`:
  - `buildPlan(params)` — формирует объект с корректным массивом `chainIds`, `salt`, `expiry`.
  - `hashPlan(plan, domain)` — получает хеш для подписи.
- Подписания:
  - `signPlan(plan, signer)` — использует seed/приватный ключ автора.
  - Хранение соли: таблица/хранилище `plan_sal` (merchant, hash, salt, status).
- CRUD операции:
  - `createPlan(plan, signature, uri)` — вызывает `PlanManager.createPlan`.
  - `activatePlan(hash)`, `deactivatePlan(hash)`, `freezePlan(hash, frozen)`, `transferPlanOwnership`.
- Получение данных:
  - `getPlan(hash)`, `listMerchantPlans(merchant)`, `listActivePlans(merchant)`.
- Сопоставление с off-chain метаданными (URI, доступы, цена в фиате).

### 3. Подписки (`subscriptions`)
- Методы для подписки пользователя:
  - `subscribe(userWallet, plan, sigMerchant, options)` — опционально формирует permit/Permit2.
  - `subscribeWithToken(...)` с расчётом `maxPaymentAmount`.
- Управление:
  - `unsubscribe(userWallet, merchant)`, `forceCancel(user, merchant, reason)`, `activateManually`.
- Чтение состояния:
  - `getSubscription(user, merchant)`, `listUserPlans(user)`, `getNativeDeposit(user)`.
- Работа с депозитами: `depositNative(user, amount, value)`, `withdrawNative(user, amount)`.
- События: подписка на `SubscriptionActivated`, `SubscriptionCharged` и запись в журнал с привязкой к пользователю.

### 4. Маркетплейс (`marketplace`)
- Генерация `SignatureLib.Listing` и EIP-712 подписей.
- Проверка валидности (expiry, chainIds, minSalt).
- Вызов `Marketplace.buy` с учётом конвертации и `maxPaymentAmount`.
- Управление ревоками: `revokeBySku`, `revokeListing`.
- Хелперы для аналитики: `listingHash(listing)`, декодирование событий `MarketplaceSale`.

### 5. Платёжный шлюз (`gateway`)
- Конфигурация шлюза для конкретного модуля (instanceId → адрес).
- Проверка поддерживаемых токенов: `assertPairSupported(tokenA, tokenB)`.
- Расчёт конвертации перед подпиской/покупкой.
- Учёт комиссий и отправка результатов в систему учёта.

### 6. Воркеры (`worker`)
- Клиент для `SubscriptionManager.charge`/`chargeBatch`:
  - Планировщик (cron/queue) и ограничение `batchLimit`.
  - Стратегия ретраев: повторная попытка при `ChargeSkipped`, вызов `markFailedCharge` при системных ошибках.
- Интеграция с текущей системой воркеров проекта:
  - Использовать существующий оркестратор заданий (например, Python/TypeScript-воркеры, если они уже задействованы в billing).
  - Добавить адаптер, который приводит формат задач к новому воркеру (очередь, ретраи, алерты).
  - При необходимости расширить рантайм: доступ к Web3-провайдеру, безопасное хранение ключей, метрики Prometheus/OTLP.
- Мониторинг:
  - Сбор метрик (успех/ошибка, latency, retried).
  - Логи с id подписки и причиной пропуска.
- CLI-интерфейс:
  - `worker run --limit <N> --dry-run`.
  - `worker reconcile --plan-hash <hash>` — ручная попытка списания.

### 7. Схемы данных и хранение (`storage`)
- **Таблица `billing_plan_signatures`**:
  - `plan_hash` (PK), `merchant_id`, `salt`, `signature`, `chain_ids`, `token`, `price`, `period`, `created_at`, `expires_at`, `metadata_uri`.
  - Используется для отслеживания солей и параметров плана, синхронизации с PlanManager.
- **Таблица `billing_subscription_state`**:
  - `user_id`, `merchant_id`, `plan_hash`, `status`, `next_charge_at`, `retry_at`, `retry_count`, `native_deposit`, `onchain_created_at`, `updated_at`.
  - Отражает данные `SubscriptionManager.SubscriptionState` плюс off-chain поля (например, `last_error`).
- **Таблица `billing_charge_attempt`**:
  - `id`, `plan_hash`, `user_id`, `tx_hash`, `status`, `error_code`, `charged_amount`, `payment_token`, `started_at`, `finished_at`, `worker_instance`.
  - Позволяет анализировать попытки воркера и хранить связь с событиями.
- **Views / Materialized views**:
  - `billing_active_plans_view` — агрегаты для операторских панелей (кол-во активных планов, выручка).
  - `billing_failed_attempts_view` — последние ошибки для алертов.
- **Кеш / KV**:
  - Redis ключи `billing:plan:{hash}` для быстрых lookup подписки/плана.
  - TTL-кеш для `plan_hash → PlanData` с invalidation при `PlanStatusChanged`.
- **Миграции**: SQL-сценарии добавляются в каталог `schema/sql/` (см. раздел в blueprint).

### 8. API-слой (`api`)
- **Админские эндпоинты**:
  - `POST /v1/billing/admin/plans` — создаёт план: принимает DTO с параметрами + подпись, вызывает `PlanService.create_plan`.
  - `PATCH /v1/billing/admin/plans/{plan_hash}` — обновление URI или статуса.
  - `POST /v1/billing/admin/plans/{plan_hash}/freeze` — форсированная заморозка (оператор).
- **Публичные эндпоинты**:
  - `GET /v1/billing/plans` — список активных планов с пагинацией, фильтрацией по мерчанту.
  - `POST /v1/billing/subscribe` — инициирует подписку; backend собирает permit/подписи, возвращает payload для кошелька.
  - `POST /v1/billing/unsubscribe` — отмена подписки, инициирует on-chain вызов (через wallet пользователя).
- **Воркеры/внутренние API**:
  - `POST /internal/billing/charge` — endpoint для ручного запуска charge (используется QA/ops).
  - gRPC/async интерфейс `subscription_service.charge_due(limit: int) -> ChargeSummary`.
- **Ответы**: включают:
  - `plan_hash`, `merchant`, `price`, `token`, `period`, `uri`, `status`, `signature`.
  - Для подписки — `txn_payload`, `deadline`, `permit`, `native_deposit_required`.
- **Валидация**: pydantic-схемы, проверяющие диапазоны цен, наличие цепи, сроки действия.

### 9. Интеграция с фронтендом / внешними сервисами
- **Frontend**:
  - Использует публичные API для отображения планов и статусов.
  - Может запрашивать `txn_payload`, после чего передает его кошельку (WalletConnect, MetaMask).
  - Получает Webhook/SSE о статусе подписки после `SubscriptionCharged`.
- **Operator UI**:
  - Подключен к админским API; показывает активность воркера, долю неудачных списаний, дашборды (см. playbook).
- **Notifications/Quota**:
  - После успешного/неуспешного биллинга библиотека публикует события (`billing.plan.changed.v1`, `billing.subscription.failed`).
  - Интеграция с нотификациями через `domains.platform.notifications` (использует существующую шину).

## Архитектура библиотеки
- **Слой transport**: Web3/Ethers провайдеры (RPC, signer).
- **Слой domain**: классы `PlanService`, `SubscriptionService`, `MarketplaceService`.
- **Слой integration**: HTTP/REST API нашего backend, который вызывает доменные методы и синхронизирует результаты с базой.
- **Слой persistence**: таблицы/коллекции для хранения солей, метаданных планов, статуса подписок, дневников воркеров.

## Конфигурация
- `CHAIN_ID` — целевая сеть.
- `CORE_SYSTEM_ADDRESS`, `PLAN_MANAGER_ADDRESS`, `SUBSCRIPTION_MANAGER_ADDRESS`, `MARKETPLACE_ADDRESS`.
- `PAYMENT_GATEWAY_ADDRESS`.
- `AUTOMATION_PRIVATE_KEY`, `AUTHOR_PRIVATE_KEY`, `OPERATOR_PRIVATE_KEY` (в dev можно один).
- `BATCH_LIMIT`, `WORKER_INTERVAL_MS`.
- `MAX_GAS_PRICE`, `GAS_LIMIT_OVERRIDES`.

## Безопасность
- Приватные ключи хранить в Secret Manager/Vault. Для dev допускается `.env`, но без коммита.
- Ограничить RPC-методы, использовать rate limit и fallback.
- Логи и события не должны содержать приватные данные пользователей (PII).
- Встроить контроль версий контрактов (ABI hash) и проверку их актуальности при старте.

## Тестирование
- Unit-тесты на генерацию планов и листингов, на корректные подписи.
- Интеграционные тесты с Hardhat:
  - Категории: `plans`, `subscriptions`, `worker`, `marketplace`.
  - Скрипты: `npm run test:billing-plans`, `npm run test:billing-worker`.
- Smoke-тест после деплоя: создаёт план, подписывает пользователя, прогоняет воркер и проверяет событие `SubscriptionCharged`.

## Roadmap развития
- Поддержка нескольких шлюзов и динамический выбор на основе токена.
- Системы нотификаций: вебхуки при `SubscriptionFailedFinal`.
- Web UI для ручного управления планами (использует библиотеку в режиме RPC-клиента).
- Автоматическое обновление `PlanManager` лимита активных планов на основе конфигурации.

## Приложения
- Пример структуры пакета:
  ```
  apps/backend/domains/platform/billing/library/
    __init__.py
    plans.py
    subscriptions.py
    marketplace.py
    gateway.py
    workers.py
    dto.py
    repositories/
      plans_repo.py
      subscriptions_repo.py
      charge_attempt_repo.py
    services/
      plan_service.py
      subscription_service.py
      marketplace_service.py
    api/
      admin.py
      public.py
      internal.py
  ```
- Основные DTO:
  - `PlanInput`, `PlanSignature`, `SubscriptionStateDTO`, `ChargeAttemptDTO`.
  - Используются как границы между REST и domain слоями.
