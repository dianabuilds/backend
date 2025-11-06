# Бэклог по внедрению биллинга EVM

Документ фиксирует полный набор работ, необходимых для интеграции смарт‑контрактов (`PlanManager`, `SubscriptionManager`, `Marketplace`) и сопутствующей инфраструктуры в текущую платформу.

## Формат
- **ID** — уникальный идентификатор задачи.
- **Тип** — Epic/Story/Task/Spike.
- **Описание** — краткое содержание.
- **Детали** — ключевые шаги/примечания.
- **Зависимости** — ссылки на связанные задачи.
- **Критерии готовности** — что должно быть выполнено.
- **Статус** — Todo / In progress / Blocked / Done.

## Epic A. Инфраструктура и конфигурация

| ID | Тип | Описание | Детали | Зависимости | Критерии готовности | Статус |
| --- | --- | --- | --- | --- | --- | --- |
| A1 | Story | Расширить DI контейнер биллинга для Web3 | Добавить фабрики Web3Provider, Signer; поддержка `BILLING_RPC_URL`, `BILLING_CHAIN_ID`, `BILLING_AUTOMATION_KEY`; интегрировать с `build_billing_container`. | — | Модуль билдится, юнит‑тесты на конфиг, в контейнере появляются сервисы `web3_provider`, `payment_gateway_client`. | Todo |
| A2 | Story | Настроить управление секретами | Выбрать источник (Vault/KMS/env). Для dev — env; для prod — Secret Manager. Описать процессы ротации. | A1 | Документация + IaC/env примеры, successful load в staging. | Todo |
| A3 | Task | Обновить Helm/Docker | Добавить переменные env, секреты, probe воркера, ресурсы. | A1, A2 | CI собирает образ с новыми env, helm release содержит значения. | Todo |
| A4 | Spike | Исследовать fallback RPC | Определить резервные RPC, схему переключения (env/feature flag). | — | Отчет с рекомендациями, выбран механизм переключения. | Todo |

## Epic B. Датастор и миграции

| ID | Тип | Описание | Детали | Зависимости | Критерии готовности | Статус |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | Story | Создать миграции БД для планов | Таблицы `billing_plan_signatures`, `billing_subscription_state`, `billing_charge_attempt`; индексы, FK; обновить ORM модели. | A1 | Миграции применяются локально и в CI, тесты схем проходят. | Todo |
| B2 | Task | Реализовать репозитории | Планов, подписок, попыток списания; кеш Redis; инвалидация по событиям. | B1 | Юнит‑тесты с SQLite/Redis, покрытие >80%. | Todo |
| B3 | Task | Написать ETL/Backfill скрипты | Для миграции существующих планов/подписок (если есть). | B1 | Скрипт dry-run, план миграции согласован. | Todo |

## Epic C. Backend‑библиотека

| ID | Тип | Описание | Детали | Зависимости | Критерии готовности | Статус |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | Story | Реализовать `PlanService` | Создание/активация/деактивация, EIP-712 подписи, валидация ролей через CoreSystem. | A1, B1 | Тесты на создание плана, проверка лимитов, интеграция с PlanManager на Hardhat. | Todo |
| C2 | Story | Реализовать `SubscriptionService` | Подписка, высвобождение депозитов, чтение состояния, интеграция с PaymentGateway. | C1 | Проходят интеграционные тесты `subscribe` + событие `SubscriptionActivated`. | Todo |
| C3 | Story | Реализовать `MarketplaceService` | Офчейн листинги, проверки, покупки с конвертацией. | C1 | Тесты `buy` с gateway mock, проверка revoked/consumed. | Todo |
| C4 | Task | DTO и схемы API | Pydantic/TypedDict для публичных и админских эндпоинтов. | C1 | JSON-схемы валидируются, тесты сериализации. | Todo |
| C5 | Task | Интеграция с Notifications/Quota | Публикация `billing.plan.changed.v1`, уведомления о неудачных оплатах. | C1, C2 | События появляются в логах, тесты на публикацию. | Todo |

## Epic D. API слой

| ID | Тип | Описание | Детали | Зависимости | Критерии готовности | Статус |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | Story | Админ API для планов | `POST /v1/billing/admin/plans`, `PATCH`, freeze/unfreeze. ACL (`support`, `billing_admin`). | C1, B2 | E2E тест: создать план, обновить URI, заморозить → PlanManager статус меняется. | Todo |
| D2 | Story | Публичный API подписки | `GET /v1/billing/plans`, `POST /v1/billing/subscribe`, `unsubscribe`. Обработка permit. | C2 | Автотест с mock wallet, проверка payload. | Todo |
| D3 | Task | Внутренний API для воркеров | `POST /internal/billing/charge`, список задолженностей. | C2 | worker вызывает HTTP/gRPC, получает ответ <200 ms. | Todo |
| D4 | Story | Operator overview расширения | Добавить метрики активных подписок, неудачных списаний, expose charge attempts в UI. | B2, C2 | Dashboard отображает данные, API отдаёт новые поля. | Todo |

## Epic E. Воркеры и автоматизация

| ID | Тип | Описание | Детали | Зависимости | Критерии готовности | Статус |
| --- | --- | --- | --- | --- | --- | --- |
| E1 | Story | Реализовать worker `billing.charge` | Наследование от `PeriodicWorker`; параметры интервала, батча; вызов `SubscriptionService.charge_due`. | C2, A1 | Воркер запускается через `python -m apps.backend.packages.worker.runner --name billing.charge`, логирование работает. | Todo |
| E2 | Task | Обновить оркестратор CLI | Добавить shortcut `python -m apps.backend.workers billing-charge`, README. | E1 | Документация обновлена, запуск без ошибок. | Todo |
| E3 | Task | Метрики и алерты | `billing_charge_success_total`, `billing_charge_failed_total`, latency histogram, алерты Prometheus. | E1 | Метрики видны в Prometheus, алерты настроены в Grafana. | Todo |
| E4 | Task | Интеграция с secret management | Воркер подтягивает ключи из Vault/KMS; тестовый режим — env. | A2, E1 | Секреты доступны, нет утечек в логах, проверено в staging. | Todo |
| E5 | Task | QA сценарии воркера | Скрипты для dry-run, stress теста, сценарии ручной проверки. | E1 | Документированы шаги, есть отчёт о тестовом прогоне. | Todo |

## Epic F. Тестирование и инфраструктура CI

| ID | Тип | Описание | Детали | Зависимости | Критерии готовности | Статус |
| --- | --- | --- | --- | --- | --- | --- |
| F1 | Story | Интеграционные тесты Hardhat | GitHub Actions job: деплой контрактов, запуск `npm run demo:subscription`, воркер в dry-run. | C1, C2, E1 | Pipeline зелёный, артефакты логов прикрепляются. | Todo |
| F2 | Task | Unit тесты библиотеки | Покрыть PlanService, SubscriptionService, MarketplaceService, Gateway client. | C1–C3 | Покрытие >80%, pytest зелёный. | Todo |
| F3 | Task | Нагрузочное тестирование | Сценарий 1000 подписок, 24h воркера, анализ метрик. | E1 | Отчёт с рекомендациями по scale, нет критических ошибок. | Todo |

## Epic G. Документация и обучение

| ID | Тип | Описание | Детали | Зависимости | Критерии готовности | Статус |
| --- | --- | --- | --- | --- | --- | --- |
| G1 | Task | Обновить `docs/playbooks/billing.md` | Добавить раздел про `billing.charge`, secret management, runbook инцидентов. | E1, A2 | Плейбук опубликован, команда support ознакомлена. | Todo |
| G2 | Task | Руководство для разработчиков | Туториал по созданию планов, запуску воркера, тестам. | C1–C2 | Документ в `docs/billing/developer-guide.md`, walkthrough проверен. | Todo |
| G3 | Task | Обучение команд | Провести сессию для support/ops, записать видео/конспект. | A2–E1 | Запись доступна, обратная связь собрана. | Todo |

## Epic H. Управление ролями и переход на прод

| ID | Тип | Описание | Детали | Зависимости | Критерии готовности | Статус |
| --- | --- | --- | --- | --- | --- | --- |
| H1 | Story | План миграции ролей | Разделение AUTHOR/OPERATOR/AUTOMATION/GOVERNOR по кошелькам, выдача через CoreSystem. | A1 | Документ с шагами и rollback, согласован с security. | Todo |
| H2 | Task | Настройка HSM/Vault | Привязка ключей к аппаратным хранилищам или Secret Manager. | A2, H1 | Ключи размещены, тестовые транзакции выполнены, аудит пройден. | Todo |
| H3 | Story | Prod readiness checklist | Smoke-тесты, мониторинг, алерты, SOP. | Все | Чеклист подписан ответственными, выдача флага на прод. | Todo |

## Epic I. Многопровайдерная интеграция

| ID | Тип | Описание | Детали | Зависимости | Критерии готовности | Статус |
| --- | --- | --- | --- | --- | --- | --- |
| I1 | Spike | Спроектировать интерфейс провайдеров платежей | Определить контракт `BillingProvider` (create/activatePlan, subscribe/charge, refund, listChains), описать routing по `chainId`/`providerId`; выпустить ADR. | A1, C1 | ADR утверждён, есть диаграмма ядро ↔ адаптеры. | Todo |
| I2 | Story | Реализовать EVM-провайдер v2 | Обобщить текущий EVM код на несколько сетей (ethereum, bsc, polygon); вынести общие части (подписи, PlanManager/SubscriptionManager вызовы), поддержать скидки и комиссии через существующие Processors. | I1, B2, C2 | Unit/интеграционные тесты проходят в трёх сетях, конфиги поддерживают множественные RPC/ключи. | Todo |
| I3 | Task | Настроить мультисетевой деплой | Скрипты деплоя контрактов (ignition/Hardhat) для каждой сети, запись адресов в конфиг, выдача ролей; обновить Helm/Docker с переменными `BILLING_NETWORKS`. | I2, A3 | Деплой в Ethereum+BSC автоматизирован, инструкции задокументированы. | Todo |
| I4 | Task | Расширить воркер/обработчики | `billing.charge` поддерживает очереди по сетям, хранит `chainId` в `billing_charge_attempt`, метрики размечены лейблом `network`. | I2, E1 | Воркер успешно обходит подписки в двух сетях, метрики разделены по сетям. | Todo |
| I5 | Story | Обновить API/админку под многосетевой режим | Каталоги планов/листингов возвращают `supportedChains`, админ может редактировать параметры сети (fees/discount modules, токены); добавить вкладку в админке с конфигом сетей. | D1–D4 | UI отображает и сохраняет настройки по каждой сети, ACL соблюдены. | Todo |
| I6 | Task | Подготовить шаблон альтернативного провайдера | Создать базовый адаптер (mock/fiat) с реализацией интерфейса, документация по подключению новых провайдеров (включая Solana как POC). | I1 | Шаблон интегрирован, тесты демонстрируют заменяемость провайдеров. | Todo |
| I7 | Task | Мультисетевые E2E тесты | Запустить сценарии подписки/покупки в Ethereum и BSC, воркер списывает обе сети; проверить скидки/комиссии. | I2, F1 | Автотесты в CI зелёные, прикладываются логи по сетям. | Todo |

## Зависимости между эпиками
- **A** → базовая конфигурация для всех остальных.
- **B** → хранилище, требуется для C/D/E.
- **C** → бизнес-логика для API и воркеров.
- **D** и **E** параллельны после завершения соответствующих сервисов.
- **F** тянет из C/D/E, но может стартовать частично раньше.
- **G** и **H** выполняются по мере готовности фичей.
- **I** опирается на A–E и задаёт направление расширения на новые сети/провайдеры.

## Общие критерии готовности программы
1. Все задачи в эпиках A–E завершены и задокументированы.
2. Метрики и алерты (E3) активны, поддержка обучена (G3).
3. Prod checklist (H3) выполнен, smoke-тесты проходят в CI и staging.
4. Документация актуальна (system-overview, backend-library, playbook, developer-guide).

## Декомпозиция и технические решения

### Epic A — Инфраструктура и конфигурация
- **A1.1**: Обновить `domains/platform/billing/wires.py` — внедрить `Web3ProviderFactory` и `SignerFactory`, принимать `BILLING_RPC_URL`, `BILLING_CHAIN_ID`, `BILLING_AUTOMATION_KEY`, валидировать цепь (`web3.eth.chain_id`).
- **A1.2**: Расширить `Settings` новыми полями `BillingWeb3Settings`; обеспечить загрузку из `.env`, Vault (через существующий loader).
- **A1.3**: Добавить ленивый клиент `PaymentGatewayClient` (использует CoreSystem.getService). Кешировать адреса сервисов и обновлять по событию.
- **A2.1**: Настроить Secret Manager/Vault: определить путь (`secret/billing/automation`), роли доступа, процедуру ротации; для dev — `.env.billing`.
- **A3.1**: Docker/Helm — добавить переменные (RPC URL, chain), смонтировать файл ключа (Kubernetes secret). Прописать liveness check `python -m apps.backend.packages.worker.runner --name billing.charge --dry-run`.
- **A4.1**: Spike: протестировать fallback RPC (Infura/Alchemy/Ankr); выбрать стратегию (round-robin vs manual switch), оформить вывод в ADR с рекомендациями.

### Epic B — Датастор и миграции
- **B1.1**: Создать миграцию `004_billing.sql`: таблицы `billing_plan_signatures`, `billing_subscription_state`, `billing_charge_attempt`; использовать `NUMERIC(78,0)` для сумм, `BYTEA` для хешей, `INTEGER[]` для chain_ids.
- **B1.2**: Добавить SQLAlchemy модели и pydantic-схемы; связать с Alembic revision.
- **B2.1**: Репозиторий планов — кеш Redis `billing:plan:{hash}`, TTL 5 мин; инвалидация по событию `PlanStatusChanged`.
- **B2.2**: Репозиторий подписок — хранить `last_error`, `worker_instance`; использовать optimistic lock по `updated_at`.
- **B2.3**: Репозиторий попыток списаний — batch insert, сохранение `gas_spent`, `payment_token`.
- **B3.1**: ETL — скрипт `scripts/billing/backfill.py`: dry-run отчёт, проверка расхождений, список ручных действий.

### Epic C — Backend-библиотека
- **C1.1**: `PlanService.create_plan` — формирует `SignatureLib.Plan`, подписывает через `eth_account.messages.encode_structured_data`, вызывает `PlanManager.createPlan`.
- **C1.2**: `PlanService.sync_plan_status` — периодический reconcile on-chain ↔ off-chain.
- **C2.1**: `SubscriptionService.subscribe_user` — формирует permit/Permit2, вызывает `SubscriptionManager.subscribe`, записывает `native_deposit`.
- **C2.2**: `SubscriptionService.charge_due` — выбирает пользователей с `next_charge_at <= now`, удерживает advisory lock (`pg_try_advisory_lock`), вызывает контракт, логирует `ChargeAttempt`.
- **C3.1**: `MarketplaceService.buy_listing` — валидирует скидки, проверяет поддержку токенов через PaymentGateway, поддерживает Permit2.
- **C4.1**: DTO — pydantic модели `PlanOut`, `SubscriptionOut`, `ChargeAttemptOut`; строгая валидация типов и диапазонов.
- **C5.1**: Интеграция событий — адаптер, публикующий `billing.plan.changed.v1`, `billing.subscription.failed` в `packages/events`.

### Epic D — API слой
- **D1.1**: FastAPI router `admin/billing.py`; зависимость `require_role("billing_admin")`; логировать каждое изменение в AuditTrail.
- **D2.1**: Public API `POST /v1/billing/subscribe` — возвращает `txn_payload` (`to`, `data`, `value`, `gas`, `chain_id`, `deadline`), rate-limit на пользователя.
- **D3.1**: Internal API `POST /internal/billing/charge` — защищено сервисным токеном/mTLS; возвращает summary (`processed`, `skipped`, `errors`).
- **D4.1**: Operator overview — расширить REST/GraphQL схемы для support, кэшировать ответы на 60 секунд.

### Epic E — Воркеры и автоматизация
- **E1.1**: Реализация `billing.charge` — класс `ChargingWorker(PeriodicWorker)`; поддержка `batch_limit`, `strict_mode`, параллельные списания через `asyncio.TaskGroup`.
- **E1.2**: Обработка ошибок — маппинг кодов (`NoPlan`, `NotDue`, `InsufficientBalance`, `PlanInactive`), повторные попытки через `retry_at`.
- **E2.1**: CLI — subparser `billing-charge` в `apps/backend/workers/__main__.py`, передающий управление runner’у, флаг `--dry-run`.
- **E3.1**: Метрики — добавить `billing_charge_success_total`, `billing_charge_failed_total`, `billing_charge_skipped_total`, histogram `billing_charge_latency_seconds`.
- **E4.1**: Secret management — воркер загружает ключ из Vault при старте, держит в памяти, очищает перед shutdown.
- **E5.1**: QA — скрипты `scripts/billing/run-charge-simulation.py`, `scripts/billing/run-worker-dry-run.sh` для стендов.

### Epic F — Тестирование
- **F1.1**: GitHub Actions job `billing-integration.yml` — запускает Hardhat, деплой контрактов, прогон `demo:subscription`, запускает воркер `--dry-run`.
- **F2.1**: Pytest модульные тесты сервисов, моки PaymentGateway, Web3.
- **F3.1**: Нагрузочный тест k6/Locust — 1000 подписок, 24h воркера, сбор Prometheus метрик.

### Epic G — Документация и обучение
- **G1.1**: Обновить playbook — разделы про воркер, секреты, алерты, ручной запуск.
- **G2.1**: Developer guide — walkthrough: деплой контрактов, создание плана, подписка, charge, просмотр метрик.
- **G3.1**: Training — материалы (презентация, запись Loom), Q&A.

### Epic H — Роли и прод
- **H1.1**: Матрица ролей и процесс выдачи; документ `docs/security/billing-roles.md`.
- **H2.1**: Интеграция с HSM/Vault — использовать signing endpoint, не выгружая ключи.
- **H3.1**: Prod checklist — шаблон release, содержит миграции, smoke, алерты, fallback RPC.
