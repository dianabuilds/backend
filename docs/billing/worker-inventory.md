# Инвентаризация текущих воркеров

Документ фиксирует существующую инфраструктуру фоновых задач в проекте и очерчивает доработки, необходимые для интеграции биллингового воркера, запускающего `SubscriptionManager.charge`/`chargeBatch`.

## 1. Текущая архитектура

### 1.1 Общий рантайм
- **Пакет**: `apps/backend/packages/worker`.
- **Ключевые классы**:
  - `Worker` — базовый интерфейс с методами `run`/`shutdown`.
  - `PeriodicWorker` + `PeriodicWorkerConfig` — периодические задачи с jitter/interval и поддержкой немедленного старта.
- **Регистрация**: `packages.worker.registry.register_worker(name)` вносит билдер в реестр, который потом запускается runner’ом.
- **Runner**: `python -m apps.backend.packages.worker.runner --name <worker>`:
  - грузит `Settings` через `load_settings`;
  - создаёт `WorkerRuntimeContext` (settings, env, logger);
  - вызывает билдер, ждёт worker и запускает его цикл `run(stop_event)`;
  - обрабатывает сигналы `SIGINT/SIGTERM` и вызывает `shutdown`.
- **Логирование**: единый формат `'%(asctime)s %(levelname)s %(name)s %(message)s'`, уровень задаётся `--log-level` или `WORKER_LOG_LEVEL`.

### 1.2 Оркестратор приложений
- **CLI**: `python -m apps.backend.workers <worker-name>`.
- **Поддерживаемые воркеры**:
  | Имя subparser | Назначение | Файл |
  | --- | --- | --- |
  | `events` | Ретрансляция доменных событий из Redis Streams | `apps/backend/workers/events_worker.py` |
  | `scheduler` | Планировщик публикаций / ан-публикаций | `apps/backend/workers/schedule_worker.py` |
  | `notifications` | Очередь уведомлений на базе `packages.worker.runner` | `apps/backend/workers/notifications_worker.py` |
  | `telemetry` | Rollup RUM событий (также через `packages.worker.runner`) | `apps/backend/workers/telemetry_worker.py` |
- **DI-контейнер**: `get_worker_container()` переиспользует `apps.backend.app.api_gateway.wires.build_container`, что обеспечивает доступ к сервисам, БД и конфигам.

### 1.3 Доменные воркеры
- **Billing**: `billing.contracts` (`apps/backend/domains/platform/billing/workers/contracts_listener.py`)
  - Наследуется от `PeriodicWorker`.
  - Использует `PeriodicWorkerConfig(immediate=True)` для быстрого старта.
  - `build_billing_container(settings=ctx.settings)` подхватывает DI-провайдер из домена.
  - Каждые `interval` секунд вызывает `service.reconcile_pending_transactions`.
  - Метрики: `worker_metrics.inc("completed" | "failed" | "idle")`.
  - Env-переменные: `BILLING_CONTRACTS_INTERVAL`, `BILLING_CONTRACTS_JITTER`, `BILLING_CONTRACTS_BATCH_LIMIT`.
- **Notifications**: `notifications.broadcast`
  - Реализован как `PeriodicWorker` с конфигом из `domains/platform/notifications/workers/broadcast.py`.
  - Интегрирован через общий runner + CLI.
- **Telemetry**: `telemetry.rum-rollup` — схожая структура, дополнительные настройки по интервалам.

### 1.4 Общие службы
- `packages.core.config.load_settings()` подтягивает конфиги из env/файлов.
- `packages.core.db.get_async_engine` + `dispose_async_engines` — управление соединениями.
- Метрики: `domains.platform.telemetry.application.worker_metrics_service.worker_metrics` предоставляет счётчики Prometheus.

## 2. Наблюдаемость и конфигурация
- **Метрики**:
  - Prometheus-счётчики `warehouse_worker_jobs_total`, `worker_metrics.inc(...)` и специализированные метрики доменов.
  - Для биллинга уже предусмотрены `worker_metrics.inc("completed"/"failed"/"idle")`.
- **Логи**:
  - Логеры именуются `worker.<name>` или доменными (`nodes.scheduler`, `events.worker`).
  - Контекст добавляется через `extra={"worker": ..., ...}`.
- **Сигналы и выключение**:
  - SIGINT/SIGTERM обрабатываются runner’ом; worker обязан завершить `run` и вызвать `shutdown`.
- **Оркестрация**:
  - Разворачивается как отдельные контейнеры/процессы, конфигурация через env.
  - Есть поддержка дополнительных аргументов (`notifications -- --once`).

## 3. Расхождения с потребностями биллинга
| Требование | Текущее состояние | Гэп | Предложение |
| --- | --- | --- | --- |
| Web3-провайдер, signer | В текущих воркерах нет интеграции с RPC/криптографиями | Нужно безопасно хранить приватный ключ `AUTOMATION_ROLE` и URL RPC | Расширить DI-контейнер: добавить сервис `Web3ProviderFactory`, конфиг `BILLING_RPC_URL`, интегрировать в `build_billing_container` |
| Управление подписками (charge) | `contracts_listener` работает с ретраями и `reconcile_pending_transactions` | Нет воркера для `SubscriptionManager.charge` | Создать новый worker `billing.charge` с периодическим обходом подписок, переиспользуя `PeriodicWorker` |
| Batch-лимиты | `BILLING_CONTRACTS_BATCH_LIMIT` уже есть | Нужно отдельное управление лимитом списаний | Ввести `BILLING_CHARGE_BATCH_LIMIT`, `BILLING_CHARGE_INTERVAL` |
| Permit/Permit2 | Не используется | Для токенов с permit нужно формировать подписи | Логика должна быть в backend-библиотеке; worker вызывает готовый сервис |
| Отчётность | Метрики `completed/failed/idle` | Для charge нужен более подробный набор | Добавить метрики: `billing_charge_success_total`, `billing_charge_failed_total`, `billing_charge_skipped_total`, `billing_charge_latency_seconds` |
| Хранение ключей | ENV-переменные/секреты в контейнерах | Для прод требуется HSM/Vault | Документировать, как worker извлекает ключ (например, через `KEYSTORE_PATH` или `AWS Secrets Manager`) |

## 4. Предлагаемые доработки
1. **Расширить контейнер биллинга**
   - Добавить фабрику `build_subscription_container` с зависимостями: PaymentGatewayClient, Web3Provider, SubscriptionRepository.
   - Поддержать конфиг `billing.automation_private_key` + `billing.rpc_url`.
2. **Новый worker `billing.charge`**
   - Реализовать аналогично `contracts_listener`, но вызывающий `subscription_service.charge_due_subscriptions(limit=X)`.
   - Регистрация через `@register_worker("billing.charge")` (в `apps/backend/domains/platform/billing/workers`).
   - Параметры: интервал, jitter, лимиты, флаг `STRICT_MODE` (для прод).
3. **Интеграция с runner**
   - Обновить `apps/backend/workers/README.md` и CLI, чтобы добавить пример запуска `python -m apps.backend.packages.worker.runner --name billing.charge`.
   - Рассмотреть shortcut в `apps/backend/workers/__main__.py` (например, subparser `billing-charge`).
4. **Metrics & Observability**
   - Расширить `worker_metrics_service` для новых метрик.
   - Добавить structured logs с `plan_hash`, `merchant`, `retry_count`.
5. **Secret management**
   - В документации описать, как worker загружает ключи (Vault, KMS, env). Для тестов оставляем env.
6. **Testing**
   - Юнит: мок `SubscriptionService`, проверка логики `charge`.
   - Интеграция: Hardhat + worker dry-run (похожий на `npm run billing:worker`).

## 5. Следующие шаги
1. Создать ADR/Issue по добавлению `billing.charge` в текущую worker-платформу.
2. Реализовать расширения DI-контейнера для доступа к Web3 и PaymentGateway.
3. Настроить конфигурацию (env vars, секреты) и обновить helm/docker чарты.
4. Обновить мониторинг/алерты (Prometheus, Grafana).
5. Перепроверить `docs/playbooks/billing.md` после внедрения, добавить раздел про новый worker.

