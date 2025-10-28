# Performance Playbook

Документ описывает повторяемый процесс контроля производительности. Он приходит на смену разовым логам и хранит только инструкции.

## Асинхронные пайплайны
- Профилируем воркеры и use-case'ы, которые влияют на `nodes`, `notifications`, `moderation`.
- Шаблон запуска локального профилирования:
  ```bash
  python -m flameprof -o var/profiling/<context>-<date>.svg -m pytest -- <module>::<test> -q
  ```
  Пример контекста: `nodes-engagement`, `notifications-worker`.
- Текстовое резюме храним рядом (`var/profiling/<context>-<date>.md`), если требуется.
- Перед профилированием отключаем шумные логгеры и убеждаемся, что фикстуры прогревают данные.

## Кэш нод
- Основная реализация — `RedisNodeCache` (TTL 300 с, лимит 5000 ключей). Настраивается переменными:
  - `APP_NODES_CACHE_TTL`
  - `APP_NODES_CACHE_MAX_ENTRIES`
- Ключи: `nodes:v1:id:<id>`, `nodes:v1:slug:<slug>`. Инвалидируем при изменении контента, тегов, встраивания.
- В тестах и офлайн-режиме используется in-memory реализация с теми же лимитами; следим, чтобы переполнение сбрасывало старые записи.
- Мониторим hit ratio через `INFO keyspace` и метрики прометея (если включены). При падении ниже 85% запускаем репрофилирование.

## Индексы и хранение
- Держим перечень критичных индексов в миграциях. При добавлении новых фильтров создаём отдельные миграции и описываем их в release notes.
- После крупных импортов или миграций выполняем `ANALYZE` и проверяем планы (`EXPLAIN ANALYZE`) для проблемных запросов.
- Храним заметки о новых индексах в комментариях миграций и, при необходимости, в ADR.

## Триггеры для повторного аудита
- Регрессия времени ответа `/v1/nodes` или `/v1/notifications` > 20%.
- Новые фильтры в админке, которые меняют шаблоны запросов.
- Изменения поставщика эмбеддингов, очередей или настроек воркеров.
- Падение hit ratio кэша ниже 85% или рост нагрузки Redis > 60% от лимита.

## Контроль и отчёты
- Результаты `scripts/api_benchmark.py`, Lighthouse и pytest coverage прикладываем в `var/` или `reports/` с датой.
- В документации (например, в `./code-audit.md`) оставляем ссылки и краткие выводы, без вставки полных логов.
- Перед релизом проверяем, что новые фичи не ломают гайд по PageHero/кэшированию и не вводят синхронные блокировки.

## Billing / Blockchain мониторинг
- Метрики:
  - `billing_transactions_total{status,network,token,source}` и `billing_transaction_value_usd_total{network,token,source}` — поток транзакций и объём.
  - `billing_subscriptions_*` (`*_active`, `*_mrr_usd`, `*_arpu_usd`, `*_churn_ratio`, `*_token_total`, `*_token_mrr_usd`, `*_network_total`) — состояние подписок и выручки.
  - `billing_transactions_network_*` (`volume`, `failed_total`, `pending_total`) — проблемные сети/токены.
  - `billing_contract_events_total{event,status,chain_id,method}` и `billing_contracts_inventory_total{label}` — активность смарт-контрактов.
- Алерты (примерные пороги, настраиваются в Grafana/Alertmanager):
  - Ошибки транзакций (`status="failed"`) >5 в течение 5 минут или доля ошибок >10% по сравнению с `status="succeeded"`.
  - Рост `pending` > 20 транзакций на протяжении 10 минут — сигнал о деградации RPC или воркера `billing.contracts`.
  - `billing_transactions_network_failed_total` > 0 на mainnet-сетях (Polygon/Arbitrum) в течение 3 минут — расследуем RPC/контракт.
  - `billing_subscriptions_churn_ratio` > 0.2 — проверяем фич-флаги и статусы тарифов.
- Дашборды дополняем ссылкой на `/v1/admin/telemetry/prometheus` (scrape Prometheus) и на overview API (`/v1/billing/overview/*`) для кросс-проверки.

## Связанные документы
- `./code-audit.md` — полный процесс аудита.
- `./security.md` — ограничения для API и фоновых воркеров.
- `../frontend/dependency-audit.md` — контроль за фронтенд-зависимостями.
